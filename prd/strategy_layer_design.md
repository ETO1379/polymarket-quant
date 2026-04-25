# Polymarket 天气量化项目：策略层设计需求与建议方案

## 1. 结论

策略层应设计为一个**可并行扩展的纯决策层**：

```text
标准化输入 StrategyContext
        ↓
多个策略并行运行 Strategy A / B / C / ...
        ↓
标准化输出 TradeSignal[]
        ↓
SignalRouter 分发给执行、存储、通知模块
```

MVP 阶段不需要复杂策略平台，但需要从一开始支持多策略并行。核心设计原则是：

```text
策略内部允许快速迭代、主观经验化；
策略外部必须接口统一、记录完整、可复盘、可扩展。
```

---

## 2. 背景与当前需求

当前项目目标不是先做研究型回测系统，而是优先上线小资金实盘交易工具。

用户已经基于个人交易经验确信存在 alpha，因此 MVP 的重点不是验证 alpha 是否存在，而是：

1. 尽快把脑内交易经验固化为可执行策略；
2. 支持 A / B / C 多个策略并行运行；
3. 用小资金实盘感受市场；
4. 保留完整记录，方便后续标准化复盘和迭代。

---

## 3. 策略层设计目标

### 3.1 MVP 阶段目标

策略层需要满足：

1. 支持多个策略并行接入；
2. 每个策略独立开发、独立启停、独立配置参数；
3. 所有策略使用统一输入格式；
4. 所有策略输出统一交易信号格式；
5. 每个信号必须能追溯到具体策略、市场、理由、时间；
6. 新增策略时尽量不改主流程。

### 3.2 暂不需要做的能力

MVP 阶段暂不做：

1. 复杂策略组合器；
2. 策略投票系统；
3. 策略评分系统；
4. 热加载策略；
5. 图形化策略配置；
6. 复杂风控模块；
7. 完整回测系统。

---

## 4. 策略层边界

策略层只做三件事：

```text
读取标准化输入 → 执行策略判断 → 输出标准化交易信号
```

策略层不负责：

| 能力 | 应归属模块 | 原因 |
|---|---|---|
| 拉取 Polymarket 数据 | DataProvider | 避免策略和数据源耦合 |
| 拉取天气数据 | DataProvider | 方便未来更换天气源 |
| 查询数据库 | Storage / ContextBuilder | 策略应尽量保持纯决策 |
| 下单 | Execution | 避免策略直接操作资金 |
| 发飞书通知 | Notification | 策略不关心通知渠道 |
| 定时调度 | Runner / Scheduler | 策略不关心运行方式 |
| 复杂风控 | Risk / SignalRouter | MVP 可先做极简拦截 |

---

## 5. 总体协作链路

推荐系统链路：

```text
Runner / Scheduler
        ↓
DataProvider
        ↓
ContextBuilder
        ↓
StrategyRegistry
        ↓
Strategy A / Strategy B / Strategy C
        ↓
TradeSignal[]
        ↓
SignalRouter
        ↓
Storage / Execution / Notification
```

### 5.1 模块职责

| 模块 | 职责 |
|---|---|
| Runner / Scheduler | 触发一次策略运行，例如每 5 分钟跑一次 |
| DataProvider | 获取 Polymarket 市场数据、订单簿、天气数据、账户持仓 |
| ContextBuilder | 把多源数据组装为标准化 StrategyContext |
| StrategyRegistry | 管理已注册策略，控制启停 |
| Strategy | 根据 StrategyContext 生成 TradeSignal |
| SignalRouter | 接收信号，进行简单去重、过滤、分发 |
| Storage | 保存信号、订单、成交、持仓快照 |
| Execution | 根据 TradeSignal 执行模拟盘或实盘下单 |
| Notification | 推送信号和交易结果 |

---

## 6. 策略输入设计：StrategyContext

### 6.1 设计原则

策略不应自己获取输入，而应接收标准化上下文对象。

```text
策略只读 StrategyContext，不直接查 API，不直接查数据库。
```

### 6.2 推荐结构

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class StrategyContext:
    run_time: datetime

    market: "MarketSnapshot"
    orderbook: Optional["OrderBookSnapshot"]
    weather: "WeatherSnapshot"
    position: Optional["PositionSnapshot"]
    account: Optional["AccountSnapshot"]
```

### 6.3 子对象示例

```python
@dataclass
class MarketSnapshot:
    market_id: str
    event_id: str
    question: str
    outcome_yes: str
    outcome_no: str
    yes_price: float
    no_price: float
    end_time: datetime
    status: str
    volume: float | None = None
    liquidity: float | None = None


@dataclass
class WeatherSnapshot:
    location: str
    forecast_time: datetime
    target_date: datetime
    metric_name: str
    forecast_value: float | None
    observed_value: float | None = None
    estimated_prob: float | None = None
    source: str | None = None


@dataclass
class PositionSnapshot:
    market_id: str
    yes_size: float
    no_size: float
    avg_price: float | None = None


@dataclass
class AccountSnapshot:
    cash: float
    total_value: float | None = None
```

MVP 阶段不需要一次性做全字段，先保留核心字段即可。

---

## 7. 策略输出设计：TradeSignal

### 7.1 设计原则

所有策略必须输出统一格式，方便后续：

1. 统一存储；
2. 统一执行；
3. 统一复盘；
4. 按策略统计表现；
5. 支持多策略并行。

### 7.2 推荐结构

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional

@dataclass
class TradeSignal:
    strategy_name: str
    market_id: str
    action: Literal["BUY", "SELL", "HOLD"]
    outcome: Literal["YES", "NO"]
    price_limit: Optional[float]
    size: Optional[float]
    confidence: Optional[float]
    edge: Optional[float]
    reason: str
    created_at: datetime
```

### 7.3 字段说明

| 字段 | 说明 |
|---|---|
| strategy_name | 生成信号的策略名称，必须有 |
| market_id | Polymarket 市场 ID |
| action | BUY / SELL / HOLD |
| outcome | YES / NO |
| price_limit | 限价，MVP 可用当前价格或固定价格 |
| size | 下单数量或金额，MVP 可按配置固定 |
| confidence | 策略置信度，可为空 |
| edge | 预估优势，例如 estimated_prob - market_price |
| reason | 策略决策理由，必须记录，便于复盘 |
| created_at | 信号生成时间 |

### 7.4 MVP 极简信号格式

若想更快实现，也可以先使用字典格式：

```python
{
    "strategy_name": "strategy_a",
    "market_id": "xxx",
    "action": "BUY",
    "outcome": "YES",
    "price_limit": 0.42,
    "size": 10,
    "reason": "estimated_prob > market_price + threshold",
    "created_at": "2026-04-25T12:00:00"
}
```

---

## 8. 多策略并行设计

### 8.1 核心思想

A / B / C 三个策略应作为三个独立类存在，而不是写在一个大 if-else 里。

```text
StrategyA(context) → signal_a
StrategyB(context) → signal_b
StrategyC(context) → signal_c
```

主流程只负责遍历策略，不关心策略内部逻辑。

---

## 9. BaseStrategy 接口

```python
from abc import ABC, abstractmethod

class BaseStrategy(ABC):
    name: str

    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get("enabled", True)

    @abstractmethod
    def generate_signal(self, context: StrategyContext) -> TradeSignal:
        raise NotImplementedError
```

---

## 10. 具体策略示例

```python
from datetime import datetime

class StrategyA(BaseStrategy):
    name = "strategy_a"

    def generate_signal(self, context: StrategyContext) -> TradeSignal:
        threshold = self.config.get("threshold", 0.08)
        size = self.config.get("size", 10)

        market_price = context.market.yes_price
        estimated_prob = context.weather.estimated_prob

        if estimated_prob is None:
            return TradeSignal(
                strategy_name=self.name,
                market_id=context.market.market_id,
                action="HOLD",
                outcome="YES",
                price_limit=None,
                size=None,
                confidence=None,
                edge=None,
                reason="missing estimated_prob",
                created_at=datetime.utcnow(),
            )

        edge = estimated_prob - market_price

        if edge > threshold:
            return TradeSignal(
                strategy_name=self.name,
                market_id=context.market.market_id,
                action="BUY",
                outcome="YES",
                price_limit=market_price,
                size=size,
                confidence=estimated_prob,
                edge=edge,
                reason=f"edge={edge:.4f}, threshold={threshold}",
                created_at=datetime.utcnow(),
            )

        return TradeSignal(
            strategy_name=self.name,
            market_id=context.market.market_id,
            action="HOLD",
            outcome="YES",
            price_limit=None,
            size=None,
            confidence=estimated_prob,
            edge=edge,
            reason=f"edge={edge:.4f} <= threshold={threshold}",
            created_at=datetime.utcnow(),
        )
```

---

## 11. StrategyRegistry 设计

### 11.1 目标

Registry 负责统一管理所有策略。

新增策略时只需要：

```text
1. 新建一个 StrategyX 类；
2. 在 registry 中注册；
3. 在配置文件中启用。
```

### 11.2 示例

```python
class StrategyRegistry:
    def __init__(self, config: dict):
        self.config = config
        self.strategies = self._load_strategies()

    def _load_strategies(self) -> list[BaseStrategy]:
        strategy_configs = self.config.get("strategies", {})

        strategies = [
            StrategyA(strategy_configs.get("strategy_a", {})),
            StrategyB(strategy_configs.get("strategy_b", {})),
            StrategyC(strategy_configs.get("strategy_c", {})),
        ]

        return [s for s in strategies if s.enabled]

    def generate_signals(self, context: StrategyContext) -> list[TradeSignal]:
        signals = []

        for strategy in self.strategies:
            signal = strategy.generate_signal(context)
            signals.append(signal)

        return signals
```

---

## 12. 策略配置设计

建议用 YAML 或 TOML。MVP 阶段一个配置文件即可。

### YAML 示例

```yaml
strategies:
  strategy_a:
    enabled: true
    size: 10
    threshold: 0.08

  strategy_b:
    enabled: true
    size: 5
    threshold: 0.12

  strategy_c:
    enabled: false
    size: 10
    threshold: 0.10
```

### 配置原则

| 配置项 | 说明 |
|---|---|
| enabled | 控制策略是否启用 |
| size | 单次下单规模 |
| threshold | 策略触发阈值 |
| strategy-specific params | 策略专属参数，放在各自节点下 |

---

## 13. SignalRouter 设计

### 13.1 MVP 阶段职责

SignalRouter 不需要做复杂风控，只做极简处理：

1. 过滤 HOLD 信号；
2. 保存所有信号；
3. 对可交易信号做去重；
4. 分发给执行模块；
5. 分发给通知模块。

### 13.2 极简冲突处理

MVP 阶段建议规则：

```text
同一 market_id + 同一 outcome + 同一 action，在同一轮运行中只允许一笔有效订单。
```

原因：避免 A / B / C 同时触发，导致重复买入。

### 13.3 示例逻辑

```python
class SignalRouter:
    def __init__(self, storage, execution, notification):
        self.storage = storage
        self.execution = execution
        self.notification = notification

    def handle_signals(self, signals: list[TradeSignal]):
        for signal in signals:
            self.storage.save_signal(signal)

        executable_signals = [s for s in signals if s.action != "HOLD"]
        executable_signals = self._deduplicate(executable_signals)

        for signal in executable_signals:
            order = self.execution.submit(signal)
            self.storage.save_order(order)
            self.notification.send_signal(signal, order)

    def _deduplicate(self, signals: list[TradeSignal]) -> list[TradeSignal]:
        seen = set()
        result = []

        for signal in signals:
            key = (signal.market_id, signal.outcome, signal.action)
            if key in seen:
                continue
            seen.add(key)
            result.append(signal)

        return result
```

---

## 14. MVP 主流程示例

```python
def run_once():
    markets = market_provider.fetch_markets()

    for market in markets:
        weather = weather_provider.fetch_weather(market.location)
        orderbook = market_provider.fetch_orderbook(market.market_id)
        position = account_provider.get_position(market.market_id)
        account = account_provider.get_account()

        context = context_builder.build(
            market=market,
            orderbook=orderbook,
            weather=weather,
            position=position,
            account=account,
        )

        signals = strategy_registry.generate_signals(context)
        signal_router.handle_signals(signals)
```

---

## 15. 推荐目录结构

```text
project_root/
  config.yaml
  main.py

  data/
    market_provider.py
    weather_provider.py
    account_provider.py

  context/
    models.py
    builder.py

  strategies/
    __init__.py
    base.py
    registry.py
    strategy_a.py
    strategy_b.py
    strategy_c.py

  signals/
    models.py
    router.py

  execution/
    executor.py

  storage/
    sqlite_storage.py

  notification/
    feishu.py
```

### 目录说明

| 目录 | 说明 |
|---|---|
| data/ | 获取外部数据 |
| context/ | 定义和构造 StrategyContext |
| strategies/ | 策略层核心目录 |
| signals/ | TradeSignal 模型和 SignalRouter |
| execution/ | 模拟盘或实盘执行 |
| storage/ | SQLite 读写 |
| notification/ | 飞书推送 |

---

## 16. MVP 策略层验收标准

策略层完成后，应满足以下标准：

1. 能同时运行 StrategyA / StrategyB / StrategyC；
2. 能通过配置文件控制每个策略启停；
3. 每个策略能读取统一 StrategyContext；
4. 每个策略能输出统一 TradeSignal；
5. 所有信号都能记录 strategy_name；
6. 新增 StrategyD 时不需要修改主流程；
7. HOLD 信号也被记录，方便复盘为什么没交易；
8. BUY / SELL 信号能被 SignalRouter 分发给执行模块；
9. 同一市场同方向信号不会重复下单；
10. 每个信号必须有 reason 字段。

---

## 17. 给 Codex 的实现要求

请 Codex 按以下原则实现策略层：

1. 不要把策略写成一个大函数；
2. 不要让策略直接调用 API；
3. 不要让策略直接写数据库；
4. 不要让策略直接下单；
5. 策略必须继承 BaseStrategy；
6. 策略必须实现 generate_signal(context)；
7. 策略输出必须是 TradeSignal；
8. 新增策略时只新增策略文件和注册配置；
9. 主流程只调用 StrategyRegistry，不直接感知具体策略；
10. MVP 优先简单可运行，不做复杂抽象。

---

## 18. 后续演进方向

V1 可以增加：

1. dry_run / live 模式切换；
2. 策略级绩效统计；
3. 信号复盘报表；
4. 策略参数统一管理；
5. 更完善的订单状态追踪。

V2 可以增加：

1. 多策略组合器；
2. 策略投票或加权；
3. 回测系统；
4. 风控模块；
5. 事件驱动架构；
6. 策略热加载；
7. 策略版本管理。

---

## 19. 一句话设计原则

```text
MVP 阶段，策略层不是研究平台，而是一个支持多策略并行的小型决策引擎。
```
