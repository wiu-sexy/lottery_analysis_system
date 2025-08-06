# 数据分析系统
<img width="677" height="468" alt="Snipaste_2025-08-06_13-23-18" src="https://github.com/user-attachments/assets/18be6bcb-f62f-49a8-8ac4-f20f56d96581" />

一个基于Flask和JavaScript的六合彩数据分析和预测系统，提供历史数据分析、趋势预测和智能预测功能。

## 功能特性

### 数据管理
- 自动获取六合彩历史开奖数据
- 数据存储和管理
- 支持数据更新和同步

### 数据分析
- 号码频率统计分析
- 冷热号码分析
- 连号和跨度分析
- 多时间段趋势分析（1年/2年/3年）

### 智能预测
- 基于历史频率的预测算法
- 基于趋势分析的预测算法
- 组合预测算法
- 预测结果置信度评估

### 可视化界面
- 响应式Web界面设计
- 实时数据展示
- 交互式图表和统计
- 移动端适配

## 技术架构

### 后端技术
- **框架**: Flask 3.1.1
- **数据库**: SQLite
- **ORM**: SQLAlchemy
- **HTTP客户端**: Requests
- **跨域支持**: Flask-CORS

### 前端技术
- **HTML5 + CSS3 + JavaScript**
- **图表库**: Chart.js
- **响应式设计**: CSS Grid + Flexbox

### 数据源
- 六合彩官方数据API
- 实时数据获取和更新

## 项目结构

```
lottery_analysis/
├── src/
│   ├── models/           # 数据模型
│   │   ├── user.py      # 用户模型
│   │   └── lottery.py   # 六合彩数据模型
│   ├── routes/          # API路由
│   │   ├── user.py      # 用户相关API
│   │   └── lottery.py   # 六合彩相关API
│   ├── services/        # 业务逻辑服务
│   │   └── lottery_service.py  # 六合彩数据服务
│   ├── static/          # 静态文件
│   │   └── index.html   # 前端界面
│   ├── database/        # 数据库文件
│   │   └── app.db       # SQLite数据库
│   └── main.py          # 应用入口
├── venv/                # Python虚拟环境
├── requirements.txt     # Python依赖
└── README.md           # 项目文档
```

## 安装和运行

### 环境要求
- Python 3.11+
- pip

### 安装步骤

1. 克隆项目到本地
```bash
cd lottery_analysis
```

2. 激活虚拟环境
```bash
source venv/bin/activate
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 运行应用
```bash
python src/main.py
```

5. 访问应用
打开浏览器访问: http://localhost:5001

## API接口

### 数据获取
- `POST /api/lottery/fetch-data` - 获取并保存六合彩数据
- `GET /api/lottery/results` - 获取开奖结果列表
- `GET /api/lottery/statistics` - 获取统计信息

### 数据分析
- `GET /api/lottery/trend-analysis` - 获取趋势分析数据
- `GET /api/lottery/number-frequency` - 获取号码频率统计
- `GET /api/lottery/consecutive-span-analysis` - 获取连号和跨度分析

### 预测功能
- `POST /api/lottery/predict` - 生成预测号码
- `GET /api/lottery/predictions` - 获取历史预测记录

## 数据模型

### LotteryResult (开奖结果)
- 期号、开奖日期、中奖号码
- 红球和蓝球分离存储
- 创建和更新时间记录

### NumberFrequency (号码频率)
- 号码出现频率统计
- 按时间段分类统计
- 最后出现时间和间隔天数

### PredictionResult (预测结果)
- 预测号码和算法信息
- 置信度评估
- 实际结果对比（待实现）

## 预测算法

### 1. 频率分析法
- 基于历史号码出现频率
- 选择热门但最近未出现的号码
- 置信度: 60%

### 2. 趋势分析法
- 分析最近期数的号码趋势
- 综合历史频率和近期表现
- 置信度: 70%

### 3. 组合预测法
- 结合频率和趋势分析
- 多算法融合预测
- 置信度: 80%

## 使用说明

### 数据获取
1. 点击"刷新数据"按钮获取最新开奖数据
2. 系统会自动从官方API获取数据并存储

### 趋势分析
1. 选择分析时间范围（1年/2年/3年）
2. 点击"分析趋势"查看热门和冷门号码
3. 查看详细的统计信息

### 智能预测
1. 选择预测算法
2. 点击"生成预测"获取预测号码
3. 查看预测置信度和算法说明
4. 可查看历史预测记录

## 注意事项

1. **仅供参考**: 本系统仅用于数据分析和学习目的，预测结果仅供参考
2. **数据准确性**: 数据来源于第三方API，请以官方开奖结果为准
3. **理性购彩**: 请理性对待彩票，不要沉迷

## 开发计划

- [ ] 添加更多预测算法
- [ ] 实现预测准确性评估
- [ ] 添加数据可视化图表
- [ ] 支持更多彩票类型
- [ ] 添加用户系统和个人预测记录

## 许可证

本项目仅用于学习。
