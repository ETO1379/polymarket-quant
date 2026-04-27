# Polymarket 天气量化：天气预报 API 选型说明

## 1. 目标

为 Polymarket 天气量化项目选择可接入的天气数据源，用于：

- 获取全球城市天气预报
- 支持天气市场概率判断
- 支持后续回测、落库、误差校准
- 优先使用免费或低成本数据源
- 尽量接近 Polymarket 市场的结算来源

核心原则：**不要只选“预报最准”的 API，而要优先匹配市场的 resolution source。**

---

## 2. 选型结论

推荐优先级：

```text
GFS / NOAA > ECMWF > Open-Meteo > CMA / 中国气象局
```

### 推荐组合

| 用途 | 推荐数据源 | 说明 |
|---|---|---|
| MVP 快速开发 | Open-Meteo | 免费、无 key、JSON API、接入最快 |
| 主预测源 | NOAA GFS | 美国官方、全球覆盖、免费、稳定 |
| 高质量对照源 | ECMWF Open Data | 欧洲官方、中期预报质量高 |
| 美国观测/预报 | NWS API / NOAA | 适合美国市场、部分结算源相关 |
| 中国区域补充 | CMA / 中国气象数据网 | 适合中国区域，不适合作为全球主源 |
| 欧洲补充 | DWD ICON / MET Norway | 可作为欧洲区域辅助模型 |

---

## 3. 重点数据源说明

## 3.1 NOAA GFS

### 定位

美国 NOAA / NCEP 的全球数值天气预报模型，适合作为项目主预测源。

### 优点

- 官方数据源
- 免费开放
- 全球覆盖
- 每天多次更新
- 数据稳定，适合自动化抓取和落库
- 与部分 Polymarket 天气市场的结算生态更接近

### 接入方式

- NOMADS HTTPS / GRIB filter
- NOAA GFS on AWS Open Data
- 数据格式主要是 GRIB2

### 问题

- 不是简单 JSON API
- 需要处理 GRIB2 文件
- MVP 阶段接入成本高于 Open-Meteo

### 使用建议

- MVP 阶段可以先用 Open-Meteo 的 GFS JSON 接口
- v1 阶段直接接入 NOAA GFS 官方数据
- 长期应作为主模型源之一

---

## 3.2 ECMWF Open Data

### 定位

欧洲中期天气预报中心的官方开放数据，适合作为高质量模型源。

### 优点

- 官方数据源
- 中期预报质量高
- 可免费使用开放数据子集
- 适合作为 GFS 的对照模型

### 接入方式

- ECMWF Open Data
- `ecmwf-opendata` Python client
- 公开云存储
- 数据格式主要是 GRIB2

### 问题

- 官方开放数据不是传统 JSON API
- 滚动保留近期 forecast run
- 直接接入复杂度高于 Open-Meteo

### 使用建议

- MVP 阶段不建议直接接 ECMWF 官方 GRIB2
- 先用 Open-Meteo 的 ECMWF 接口快速验证
- v1/v2 阶段再接官方 ECMWF Open Data

---

## 3.3 Open-Meteo

### 定位

非官方天气数据聚合 API，适合 MVP 快速开发。

### 优点

- 免费可用，非商业场景友好
- 无需 API key
- REST / JSON API
- 支持 GFS、ECMWF、DWD、JMA、MET Norway 等模型
- 接入成本最低

### 问题

- 不是官方数据源
- 商业使用需要确认其条款
- 不适合作为最终唯一数据源

### 使用建议

- MVP 阶段优先接入
- 用于快速跑通：城市坐标 → 小时级预报 → 策略信号
- 后续用官方 GFS / ECMWF 替代或校验

---

## 3.4 CMA / 中国气象局 / 中国气象数据网

### 定位

中国官方气象数据源，适合中国区域天气数据补充。

### 优点

- 官方来源
- 有中国区域观测、预报、历史数据等资源
- 部分服务支持 API / WebService

### 问题

- 通常需要注册、申请或确认权限
- 免费边界和调用限制需要逐数据集确认
- 全球覆盖和自动化友好程度不如 NOAA
- 与 Polymarket 全球天气市场结算源匹配度较低

### 使用建议

- 不建议作为项目主数据源
- 可作为中国区域市场的补充数据源
- 后续再评估是否接入

---

## 4. 项目接入阶段建议

## 4.1 MVP 阶段

目标：快速跑通天气市场信号生成。

优先做：

1. 接入 Open-Meteo JSON API
2. 支持按城市经纬度获取小时级预报
3. 保存 forecast 数据到 SQLite
4. 解析 Polymarket market rules 中的结算来源
5. 输出简单概率判断和交易信号

暂不做：

- 不直接处理 GRIB2
- 不做复杂 ensemble
- 不接多个官方数据源
- 不做重型历史回测系统

---

## 4.2 v1 阶段

目标：提升数据可靠性和交易可解释性。

增加：

1. 直接接入 NOAA GFS 官方数据
2. 按 market 维护结算源映射
3. 引入站点级观测数据
4. 对模型预报做站点偏差校准
5. 增加 forecast 版本管理

---

## 4.3 v2 阶段

目标：从点预测升级为概率分布预测。

增加：

1. 接入 ECMWF Open Data
2. 引入 GFS Ensemble / ECMWF Ensemble
3. 建立多模型融合
4. 计算不同模型分歧度
5. 输出概率分布，而不是单一温度预测

---

## 5. 给 AI Coding 的实现要求

### 数据源抽象

请设计统一的 weather provider 接口，不要把 Open-Meteo、GFS、ECMWF 的逻辑写死在策略层。

建议抽象：

```text
WeatherProvider
- get_forecast(location, start_time, end_time)
- get_observation(location, start_time, end_time)
- get_metadata()
```

每个数据源单独实现：

```text
OpenMeteoProvider
GFSProvider
ECMWFProvider
CMAProvider
```

### 数据存储原则

forecast 数据要保存以下核心字段：

```text
source
model
run_time
forecast_time
location_id
lat
lon
variable
value
unit
raw_payload_path / raw_data_ref
created_at
```

### 策略层原则

策略层不直接调用具体 API。

策略层只消费标准化后的天气数据：

```text
market_id
target_location
target_datetime
target_variable
forecast_value
forecast_probability
source
model
```

### 关键约束

1. 先实现 Open-Meteo，保证 MVP 快速可用
2. 保留未来接入 GFS / ECMWF 官方数据的扩展口
3. 不要把数据源与交易策略强耦合
4. 每条预测数据必须保留 source 和 run_time
5. 每个 Polymarket market 必须维护 resolution source，不要默认统一结算源

---

## 6. 最小开发任务拆解

### Task 1：实现 Open-Meteo Provider

输入：

```text
lat, lon, start_time, end_time, variables
```

输出：

```text
标准化 forecast records
```

### Task 2：设计 weather forecast 落库

使用 SQLite。

要求：

- 支持按 source / model / run_time 查询
- 支持按 location + forecast_time 查询
- 支持后续迁移到 PostgreSQL

### Task 3：设计 market-resolution 映射

维护：

```text
market_id
event_id
city
station_id
resolution_source
resolution_url
target_variable
target_datetime
timezone
unit
```

### Task 4：策略层读取天气数据

策略层只读取标准化 forecast，不关心底层 API。

输出：

```text
market_id
side
expected_probability
market_price
edge
signal_strength
reason
```

---

## 7. 重要原则

Polymarket 天气量化的核心不是单纯获取天气预报，而是：

```text
结算源识别 → 天气预测 → 偏差校准 → 概率估计 → 价格比较 → 交易信号
```

因此，天气 API 选型必须服务于交易闭环，而不是为了接入更多数据源。
