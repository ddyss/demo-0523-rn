# 秒杀扣库存防超卖 - 实战学习方案

## 学习目标

通过一个经典高并发场景（秒杀扣库存），亲手体验：
1. 并发问题是怎么产生的（竞态条件、超卖）
2. 数据库锁怎么解决（悲观锁/乐观锁）
3. Redis + Lua 怎么做到高性能且不超卖
4. 缓存与数据库的最终一致性

每个阶段都有"压测验证"，不压测 = 没学过。

## 场景

商品秒杀：库存 1000 件，模拟 1000+ 并发用户抢购，要求不超卖、不少卖。

## 技术栈

- 语言：Python 3（最快跑通，专注并发问题本身而非框架）
- MySQL：在线实例（连接信息待补充）
- Redis：在线实例（已有，见 redis配置.md）
- 压测：Python `concurrent.futures` 多线程脚本（零依赖，够用）

---

## 数据准备

### MySQL 建表

```sql
CREATE TABLE stock (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    product_id BIGINT NOT NULL,
    stock_count INT NOT NULL,          -- 剩余库存
    version INT NOT NULL DEFAULT 0,    -- 乐观锁版本号
    UNIQUE KEY uk_product (product_id)
);

INSERT INTO stock (product_id, stock_count) VALUES (1001, 1000);

-- 记录每次下单，用于核对订单数是否 <= 库存
CREATE TABLE stock_order (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    product_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Redis 初始化

```
SET stock:1001 1000
```

---

## 阶段1：发现问题 - MySQL 裸扣（体验超卖）

### 思路
先查库存 >0，再扣减。两步非原子，并发下会超卖。

### 关键代码
```python
# 错误写法：查 + 判 + 减，三步非原子
def deduct_stock_wrong(conn, product_id, user_id):
    cur = conn.cursor()
    cur.execute("SELECT stock_count FROM stock WHERE product_id=%s", (product_id,))
    count = cur.fetchone()[0]
    if count <= 0:
        return False  # 卖完了
    # ⚠️ 并发到这里时，别的线程也查到了 count>0，都进来扣减 → 超卖
    cur.execute("UPDATE stock SET stock_count=stock_count-1 WHERE product_id=%s", (product_id,))
    cur.execute("INSERT INTO stock_order (product_id, user_id) VALUES (%s,%s)", (product_id, user_id))
    conn.commit()
    return True
```

### 压测验证
- 1000 库存，开 200 个线程各抢 10 次（共 2000 次请求）
- 预期现象：`stock_count` 变成负数，`stock_order` 记录数 > 1000 → **超卖**
- 学到：竞态条件、读改写非原子性

---

## 阶段2：解决问题 - MySQL 乐观锁（正确但慢）

### 思路
用 `WHERE stock_count > 0` 把"判断+扣减"合成一条原子 SQL，数据库保证不超卖。

### 关键代码
```python
# 正确写法：一条 UPDATE 带条件，原子操作
def deduct_stock_ok(conn, product_id, user_id):
    cur = conn.cursor()
    # 只当库存>0 时才扣成功，affected_rows=0 说明没抢到
    cur.execute("UPDATE stock SET stock_count=stock_count-1 WHERE product_id=%s AND stock_count>0", (product_id,))
    if cur.rowcount == 0:
        return False  # 没抢到
    cur.execute("INSERT INTO stock_order (product_id, user_id) VALUES (%s,%s)", (product_id, user_id))
    conn.commit()
    return True
```

### 压测验证
- 同样 2000 次请求
- 预期现象：`stock_count` 最终 = 0，`stock_order` 记录数 = 1000 → **不超卖**
- 但 QPS 低（数据库行锁竞争 + 网络往返）
- 学到：原子操作、行锁、数据库事务

### 对比实验（可选）
- 悲观锁 `SELECT ... FOR UPDATE`：也防超卖，锁持有更久，QPS 更低
- 乐观锁 `version`：`UPDATE ... SET version=version+1 WHERE id=? AND version=?`，高并发下重试多

---

## 阶段3：高性能方案 - Redis + Lua（快且不超卖）

### 思路
库存预热到 Redis，用 Lua 脚本原子扣减（判断+扣减在 Redis 单线程内一次完成）。
Redis 扣减成功 = 抢到了，再异步写 MySQL 订单。

### Lua 脚本
```lua
-- deduct.lua
-- KEYS[1] = stock:1001
-- ARGV[1] = 扣减数量(1)
local stock = tonumber(redis.call('GET', KEYS[1]))
if stock == nil then
    return -1  -- 库存未初始化
end
if stock < tonumber(ARGV[1]) then
    return 0   -- 库存不足，抢购失败
end
redis.call('DECRBY', KEYS[1], ARGV[1])
return 1       -- 抢购成功
```

### 关键代码
```python
import redis

r = redis.Redis.from_url("redis://default:xxx@redis-12922...:12922")
DEDUCT_SCRIPT = """..."""  # 上面的 lua

def deduct_stock_redis(product_id, user_id):
    # Lua 原子扣减，返回 1=成功 0=售罄
    res = r.eval(DEDUCT_SCRIPT, 1, f"stock:{product_id}", 1)
    if res == 1:
        # 异步写订单到 MySQL（阶段4再处理一致性）
        return True
    return False
```

### 压测验证
- 同样 2000 次请求
- 预期现象：不超卖，**QPS 比 MySQL 方案高一个数量级**（Redis 内存操作 + 单线程无锁竞争）
- 学到：Redis 单线程模型、Lua 原子性、为什么 Redis 比 DB 快

---

## 阶段4：最终一致 - Redis 扣减成功后异步同步 MySQL

### 思路
Redis 扣减成功后，订单记录要落库。但同步写 MySQL 会拖慢。
用"异步"：Redis 扣减成功立即返回用户"抢到了"，后台线程把订单写进 MySQL。

### 关键问题（要思考的）
1. Redis 扣减成功了，但写 MySQL 订单前程序崩了 → 怎么办？
2. 用户看到"抢到了"，但订单没落库 → 怎么发现？
3. 这就是"最终一致性" vs "强一致性"的取舍

### 简单实现
```python
from concurrent.futures import ThreadPoolExecutor
order_pool = ThreadPoolExecutor(max_workers=4)

def deduct_stock_final(product_id, user_id):
    res = r.eval(DEDUCT_SCRIPT, 1, f"stock:{product_id}", 1)
    if res == 1:
        # 异步落库：先返回用户成功，后台写订单
        order_pool.submit(async_save_order, product_id, user_id)
        return True
    return False

def async_save_order(product_id, user_id):
    # 写订单 + 同步扣减 MySQL 库存（对账用）
    conn = get_mysql_conn()
    cur = conn.cursor()
    cur.execute("UPDATE stock SET stock_count=stock_count-1 WHERE product_id=%s AND stock_count>0", (product_id,))
    cur.execute("INSERT INTO stock_order (product_id, user_id) VALUES (%s,%s)", (product_id, user_id))
    conn.commit()
```

### 压测验证
- 用户响应极快（只有 Redis 操作）
- 等 1-2 秒后查 MySQL，订单数 = 1000，库存 = 0
- 故意 kill 程序 → 观察是否有订单丢失（这就是一致性问题）

### 进阶思考（不用实现，想清楚即可）
- 生产环境用消息队列（RabbitMQ/Kafka）替代线程池，保证消息不丢
- 用 Redis 的 RDB/AOF 保证 Redis 数据不丢
- 对账：定时核对 Redis 库存 == MySQL 库存

---

## 压测脚本模板

```python
import concurrent.futures
import pymysql

def stress_test(func, product_id, total=2000, workers=200):
    """通用压测：func=扣库存函数, total=总请求数, workers=并发线程数"""
    success = 0
    fail = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(func, product_id, i) for i in range(total)]
        for f in concurrent.futures.as_completed(futures):
            if f.result():
                success += 1
            else:
                fail += 1
    print(f"成功: {success}, 失败: {fail}")
    # 查实际库存和订单数核对
```

---

## 每阶段验收标准

| 阶段 | 必须验证的现象 | 学到什么 |
|---|---|---|
| 1 裸扣 | 超卖（库存变负） | 竞态条件 |
| 2 MySQL锁 | 不超卖，QPS低 | 行锁、原子SQL、事务 |
| 3 Redis+Lua | 不超卖，QPS高10倍 | Redis单线程、Lua原子性 |
| 4 异步落库 | 快速响应+最终一致 | 缓存DB一致性、异步、对账 |

---

## 待补充

- [ ] MySQL 在线实例连接信息（host/port/user/password/db）
- [ ] 本地 Python 环境（`pip install redis pymysql`）
