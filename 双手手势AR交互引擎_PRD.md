# GesturaX — 双手手势 AR 交互引擎

> **项目代号：GesturaX** ｜ 版本：v1.0 ｜ 更新日期：2025-07-10

---

## 1. 需求描述 (Requirements)

### 1.1 项目背景

随着 Web 端 AI 推理能力的快速发展，浏览器已经可以实时运行轻量级视觉模型，无需后端服务器。**GesturaX** 旨在探索这一能力的极限——通过摄像头实时捕捉用户双手的三维空间姿态，在视频画面上叠加动态几何光效，打造一款具有未来感的 AR 人机交互体验。

本项目面向以下使用场景：
- **展会与演示**：作为交互式装置，吸引观众参与体验
- **教育与科普**：直观展示计算机视觉与 AI 能力
- **创意工作室**：作为视觉表演工具，配合音乐或演讲
- **技术原型验证**：验证 Web AR 实时渲染的可行性边界

### 1.2 核心问题定义

传统 AR 应用依赖原生 App 或专用硬件，部署成本高、用户门槛高。本项目解决三个关键问题：

| 问题 | 解决方案 |
|------|----------|
| 手势检测需要高性能设备 | MediaPipe WASM 推理，兼容中低端设备 |
| AR 效果渲染卡顿 | 双层 Canvas 异步渲染，主线程与绘制分离 |
| 关键点坐标抖动 | LERP 线性插值平滑算法，动态调节系数 |

### 1.3 用户故事

```
作为一名展会参观者，
我希望站在摄像头前举起双手，
能够看到我的手指之间出现发光的几何图形，
以便感受到 AI 实时识别的神奇体验。

作为一名开发者，
我希望能通过控制面板实时调整视觉效果参数，
以便快速迭代不同的视觉风格，
而无需修改代码重新编译。
```

### 1.4 非功能需求

- **性能**：目标帧率 ≥ 30 FPS（普通笔记本），理想状态 60 FPS
- **延迟**：手势到光效的端到端延迟 ≤ 100ms
- **兼容性**：支持 Chrome 90+、Edge 90+、Safari 15+（需 HTTPS）
- **分辨率**：推荐摄像头输入 1280×720，自动降级至 640×480
- **隐私安全**：所有推理在本地完成，不上传任何摄像头数据

---

## 2. 核心功能 (Features)

### 2.1 实时手势追踪

GesturaX 采用 **MediaPipe Hand Landmarker** 作为核心检测引擎，支持同时追踪双手的完整骨架。

**关键点分布（每只手 21 个点）：**

```
手腕 (0)
  ├── 大拇指: 1(CMC) → 2(MCP) → 3(IP) → 4(TIP)
  ├── 食指:   5(MCP) → 6(PIP) → 7(DIP) → 8(TIP)  ← 核心交互点
  ├── 中指:   9(MCP) → 10(PIP) → 11(DIP) → 12(TIP)
  ├── 无名指: 13(MCP) → 14(PIP) → 15(DIP) → 16(TIP)
  └── 小指:   17(MCP) → 18(PIP) → 19(DIP) → 20(TIP)
```

**追踪技术指标：**
- 检测模型大小：约 8.3 MB（WASM 格式）
- 推理精度：关键点定位误差 < 5px（720p 输入）
- 支持手部遮挡情况下的关键点预测（插值补全）
- 输出坐标系：归一化 [0,1] 范围，需乘以 Canvas 尺寸转换为像素坐标

### 2.2 动态 AR 视觉效果

#### 2.2.1 发光三角形（Core Effect）

以双手的三个关键锚点构成三角形顶点：

| 顶点 | 来源 | 关键点索引 |
|------|------|-----------|
| 顶点 A | 左手食指尖 | Left Hand #8 |
| 顶点 B | 右手食指尖 | Right Hand #8 |
| 顶点 C | 双手拇指中点 | (Left #4 + Right #4) / 2 |

渲染参数：
- 描边颜色：当前主题色 `glow`，线宽 2px
- 外发光：`shadowBlur: 20`，`shadowColor: glow`
- 填充：`createRadialGradient` 从三角形重心向外渐变
- 透明度脉冲：`opacity = 0.4 + 0.3 * sin(Date.now() / 600)`（呼吸灯效果）

#### 2.2.2 网格扫描线（Scanline Grid）

限制在三角形区域内部，模拟全息投影扫描效果：

- 使用 `ctx.clip()` 将绘制区域裁切至三角形路径
- 横向扫描线：间距 `gridSpacing`（可调），颜色为主题 `glow` 色，透明度 30%
- 纵向扫描线：与横向正交，同样裁切
- 位移驱动：`offset = (Date.now() / 60) % gridSpacing`，实现匀速流动
- 扫描方向：从上到下，速度与 Lerp 平滑系数关联

#### 2.2.3 连接光束（Beam Lines）

手掌关键点（掌心 #0、指根 #5、#9、#13、#17）向三角形重心发射虚线连接：

- 线型：`setLineDash([4, 8])`
- 颜色：主题 `top` 色，透明度随距离衰减
- 粗细：1px，边缘 `shadowBlur: 8`
- 端点装饰：关键点处绘制半径 3px 的发光圆点

#### 2.2.4 关键点标注层

所有 21 个关键点的可视化标注：

- 普通关键点：白色小圆点，半径 2px
- 核心交互点（#4、#8）：主题色大圆点，半径 5px，带发光效果
- 骨骼连线：手指各段之间的连线，颜色为 `rgba(255,255,255,0.3)`

### 2.3 颜色主题系统

预设 5 种精美色系，支持运行时一键切换：

```javascript
const COLOR_THEMES = [
  {
    name: "赛博 Cyber",
    top: "rgba(0, 255, 255, 0.6)",
    bottom: "rgba(255, 0, 255, 0.6)",
    glow: "#00ffff"
  },
  {
    name: "烈焰 Flame",
    top: "rgba(255, 200, 0, 0.6)",
    bottom: "rgba(255, 50, 0, 0.6)",
    glow: "#ffaa00"
  },
  {
    name: "皇家 Royal",
    top: "rgba(160, 32, 240, 0.6)",
    bottom: "rgba(255, 215, 0, 0.6)",
    glow: "#a020f0"
  },
  {
    name: "深海 Ocean",
    top: "rgba(0, 191, 255, 0.6)",
    bottom: "rgba(0, 250, 154, 0.6)",
    glow: "#00bfff"
  },
  {
    name: "红绿 Matrix",
    top: "rgba(255, 50, 50, 0.6)",
    bottom: "rgba(50, 255, 50, 0.6)",
    glow: "#00ff88"
  }
];
```

### 2.4 智能交互 UI

#### 控制面板参数清单

| 参数项 | 类型 | 默认值 | 范围 | 说明 |
|--------|------|--------|------|------|
| 平滑度（Lerp） | Slider | 0.15 | 0.05 ~ 0.5 | 值越小越平滑，延迟越高 |
| 网格间距 | Slider | 20px | 10 ~ 50px | 扫描线密度 |
| 发光强度 | Slider | 20 | 5 ~ 40 | shadowBlur 值 |
| 颜色主题 | Select | 赛博 | 5 种 | 实时切换色系 |
| 演示模式 | Toggle | OFF | — | 无需真实手势，播放预设动画 |
| 摄像头 | Toggle | ON | — | 暂停/恢复摄像头画面 |
| 关键点显示 | Toggle | ON | — | 是否显示骨骼关键点标注 |
| 扫描线显示 | Toggle | ON | — | 是否显示三角形内部网格 |

#### UI 交互规范

- 控制面板默认**收起**，点击右上角齿轮图标展开
- 展开动画：从右上角向左下方展开，使用 `spring` 弹性动画（stiffness: 300）
- 收起时保留半透明背景按钮，不遮挡 AR 效果区域
- FPS 与延迟数据每秒更新一次，使用 `font-mono` 等宽字体

### 2.5 演示模式（Demo Mode）

当摄像头不可用或用于展示时，演示模式自动播放预设手势动画：

- 双手虚拟关键点按椭圆轨迹缓慢运动
- 三角形顶点随时间做正弦波动
- 整体效果与真实手势检测视觉一致
- 背景替换为深灰色纯色，突出光效

### 2.6 性能监测

实时显示以下系统指标（左上角 HUD 样式）：

```
● FPS: 58        ← 绿色（≥30）/ 黄色（15~29）/ 红色（<15）
● LATENCY: 17ms  ← 推理耗时
● HANDS: 2       ← 当前检测到的手部数量
● MODE: LIVE     ← LIVE / DEMO
```

---

## 3. 技术栈 (Tech Stack)

| 分类 | 技术选型 | 版本 | 说明 |
|------|----------|------|------|
| **前端框架** | React + TypeScript | 18/19 | Hooks 架构，严格类型 |
| **AI 视觉库** | `@mediapipe/tasks-vision` | latest | WASM 推理，无需 GPU |
| **渲染引擎** | HTML5 Canvas 2D | 原生 | 双层叠加渲染 |
| **动画库** | `motion`（Framer Motion） | 11+ | 弹性动画与过渡 |
| **样式方案** | Tailwind CSS | 4.0 | JIT 原子化 CSS |
| **图标库** | `lucide-react` | latest | Settings / Camera 图标 |
| **构建工具** | Vite | 5+ | 热更新、WASM 支持 |
| **类型检查** | TypeScript | 5+ | 严格模式 |
| **包管理** | npm / pnpm | — | 推荐 pnpm |

### 3.1 关键依赖说明

**MediaPipe Tasks Vision**
- 使用 `FilesetResolver` 加载 WASM 运行时
- `HandLandmarker.createFromOptions()` 初始化检测器
- 模型文件通过 CDN 异步加载，首次加载约 3~5 秒

**Canvas 双层架构**
```
<div class="relative">
  <video ref={videoRef} />           ← 隐藏的视频源
  <canvas ref={bgCanvasRef} />       ← 第一层：镜像视频
  <canvas ref={arCanvasRef} />       ← 第二层：AR 光效（叠加）
</div>
```

---

## 4. 开发指令 (Prompt Content)

> 以下为完整的 AI 开发提示词，可直接用于 Claude / GPT / Cursor 等工具。

---

### 完整 Prompt（可直接复制使用）

```
请根据以下技术规范，完整开发一个名为 GesturaX 的双手指尖交互 AR Web 程序。

【技术环境】
- 使用 Vite + React 18 + TypeScript 初始化项目
- 安装依赖：@mediapipe/tasks-vision, motion, lucide-react, tailwindcss@4.0
- 配置 Vite 以支持 WASM 文件（添加 optimizeDeps.exclude: ['@mediapipe/tasks-vision']）
- vite.config.ts 中设置 headers: { 'Cross-Origin-Opener-Policy': 'same-origin' }

【核心模块一：HandLandmarker 初始化】
- 创建 useHandLandmarker() 自定义 Hook
- 使用 FilesetResolver.forVisionTasks() 加载 WASM
- HandLandmarker.createFromOptions() 参数：
    baseOptions.modelAssetPath: CDN 路径
    runningMode: "VIDEO"
    numHands: 2
    minHandDetectionConfidence: 0.5
    minHandPresenceConfidence: 0.5
    minTrackingConfidence: 0.5
- 返回 landmarker 实例，加载中显示进度状态

【核心模块二：摄像头视频流】
- 创建 useCamera() 自定义 Hook
- 调用 navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720 } })
- 将流赋值给 video 元素的 srcObject，等待 onloadedmetadata 后 play()
- 提供 isCameraOff 切换开关，暂停时停止帧检测循环

【核心模块三：LERP 平滑算法】
- 创建 useSmoothLandmarks() Hook，接收 rawLandmarks 和 alpha 参数
- 实现：smooth = prev + alpha * (current - prev)
- 对每只手的 21 个关键点的 x, y, z 分别独立平滑
- alpha 范围 0.05（极平滑）至 0.5（接近原始），默认 0.15
- 使用 useRef 存储上一帧数据，避免触发 re-render

【核心模块四：Canvas 渲染引擎】
使用 requestAnimationFrame 驱动渲染循环：

步骤 1 - 绘制视频层（bgCanvas）：
  ctx.save()
  ctx.scale(-1, 1)  // 水平镜像
  ctx.translate(-width, 0)
  ctx.drawImage(videoRef.current, 0, 0, width, height)
  ctx.restore()

步骤 2 - 调用 landmarker.detectForVideo(video, timestamp)

步骤 3 - 清空 arCanvas，绘制 AR 效果：
  3a. 遍历检测到的手部，绘制骨骼关键点（小圆点 + 连线）
  3b. 若检测到双手：
      - 计算 tipA = 左手食指尖 index 8（镜像后的坐标）
      - 计算 tipB = 右手食指尖 index 8
      - 计算 tipC = (左手拇指尖 + 右手拇指尖) / 2
      - 绘制三角形路径 Path2D
      - 应用径向渐变填充（从重心向外，top→bottom 颜色）
      - 描边发光：ctx.shadowBlur=20, ctx.shadowColor=glow
      - ctx.save() → ctx.clip() → 绘制网格扫描线 → ctx.restore()
  3c. 绘制虚线连接光束（掌心到三角形重心）

步骤 4 - 更新 FPS 计数（每 30 帧平均一次）

【核心模块五：颜色主题系统】
- 定义 COLOR_THEMES 数组（5 种主题，含 name/top/bottom/glow 字段）
- useTheme() Hook 管理当前主题索引
- 主题切换时无需重新初始化，仅更新绘制参数

【UI 组件：ControlPanel】
- 使用 AnimatePresence + motion.div 实现面板动画
- 展开动画：opacity 0→1，y -20→0，duration 0.3s
- 面板定位：fixed 右上角，z-index 50
- 毛玻璃效果：bg-black/60 backdrop-blur-xl rounded-2xl border border-white/10
- 内部使用 Slider（range input）和 Toggle（checkbox 美化）组件
- 标题字体：text-xs font-mono text-cyan-400/80

【HUD 信息面板】
- 定位：fixed 左上角，字体 font-mono text-xs
- FPS 颜色：green(≥30) / yellow(15~29) / red(<15)
- 显示字段：FPS / LATENCY / HANDS / MODE

【演示模式】
- Demo 模式下，生成虚拟关键点：
  leftTip = { x: 0.3 + 0.1*sin(t), y: 0.4 + 0.1*cos(t) }
  rightTip = { x: 0.7 + 0.1*cos(t), y: 0.4 + 0.1*sin(t) }
  thumbMid = { x: 0.5, y: 0.6 + 0.05*sin(t*2) }
- 背景替换为纯色 #0a0a0a

【样式规范 - Cosmic Noir】
- 全局背景：#0a0a0a（近黑深灰）
- 主色调：cyan-400 (#22d3ee) / emerald-400 (#34d399)
- 边框：white/10（极低透明度白色）
- 字体：font-mono（等宽，科技感）
- 圆角：rounded-xl / rounded-2xl
- 所有交互元素加 transition-all duration-200

【类型定义（types.ts）】
interface HandLandmark { x: number; y: number; z: number }
interface ColorTheme { name: string; top: string; bottom: string; glow: string }
interface Settings {
  alpha: number;        // LERP 平滑系数
  gridSpacing: number;  // 扫描线间距
  glowIntensity: number;// 发光强度
  themeIndex: number;   // 当前主题索引
  showKeypoints: boolean;
  showScanlines: boolean;
}
interface AppState {
  settings: Settings;
  isCameraOff: boolean;
  isDemoMode: boolean;
  showPanel: boolean;
}
```

---

### 4.1 分步开发建议（给 AI 工具的迭代 Prompt）

**Step 1 — 基础框架搭建**
```
仅搭建 Vite+React+TS 项目结构，配置 Tailwind 4.0，
创建空的 App.tsx，显示 "GesturaX" 标题文字，黑色背景。
不包含任何 MediaPipe 代码。
```

**Step 2 — 摄像头接入**
```
在 Step 1 基础上，添加 useCamera() Hook，
接入摄像头视频流并在 Canvas 上绘制镜像视频。
不包含手势检测，只显示摄像头画面。
```

**Step 3 — 手势检测接入**
```
在 Step 2 基础上，集成 MediaPipe HandLandmarker，
检测到手势后在 Canvas 上绘制所有关键点（白色圆点）和骨骼连线。
实现 LERP 平滑算法。
```

**Step 4 — AR 光效渲染**
```
在 Step 3 基础上，当检测到双手时：
1. 绘制发光三角形（食指尖 + 拇指中点）
2. 三角形内部绘制网格扫描线
3. 添加虚线连接光束
使用默认 Cyber 主题色。
```

**Step 5 — 控制面板与主题系统**
```
在 Step 4 基础上，添加：
1. 右上角可折叠 ControlPanel（AnimatePresence 动画）
2. 5 种颜色主题切换
3. 左上角 HUD 信息面板（FPS/延迟/手部数量）
4. 演示模式开关
```

---

## 5. 数据流架构

```
摄像头硬件
    │
    ▼
getUserMedia() → videoElement
    │
    ▼
requestAnimationFrame 主循环
    │
    ├──► bgCanvas.drawImage(video)  ← 镜像视频渲染
    │
    ├──► landmarker.detectForVideo() ← MediaPipe 推理
    │         │
    │         ▼
    │    rawLandmarks (21点 × 双手)
    │         │
    │         ▼
    │    LERP 平滑处理
    │         │
    │         ▼
    │    smoothLandmarks
    │
    └──► arCanvas 绘制引擎
              │
              ├── 关键点标注层
              ├── 三角形 + 渐变填充
              ├── 网格扫描线（clip 裁切）
              └── 连接光束

状态管理 (React useState)
    ├── AppState → 控制面板 → 参数调节
    └── ColorTheme → 主题系统 → Canvas 绘制参数
```

---

## 6. 项目现状总结

| 模块 | 完成状态 | 说明 |
|------|----------|------|
| **Visual Identity** | ✅ 已完成 | 高对比度科技感界面，Cosmic Noir 风格，实时关键点标注 |
| **AR Effects** | ✅ 已完成 | 动态三角形、径向渐变、网格扫描线及呼吸灯脉冲效果 |
| **Interaction** | ✅ 已完成 | 设置按钮 + 控制面板按需展示，优化屏幕空间利用率 |
| **Color Themes** | ✅ 已完成 | 5 种色系预设，运行时一键切换 |
| **演示模式** | 🔄 进行中 | 基础动画完成，待优化轨迹自然度 |
| **性能 HUD** | 🔄 进行中 | FPS 显示完成，延迟计算待优化 |
| **移动端适配** | ⏳ 待开发 | 触屏设备摄像头兼容性验证 |
| **手势快捷操作** | ⏳ 待开发 | 捏合手势触发特效切换 |

---

## 7. 后续迭代方向

### 7.1 功能增强
- **手势识别语义化**：识别"OK""点赞""剪刀手"等手势，触发不同视觉效果
- **音乐联动**：接入 Web Audio API，让光效随音乐节奏跳动
- **多边形扩展**：当检测到 3 只手（双手 + 额外手势）时，生成五边形或星形

### 7.2 性能优化
- 使用 **OffscreenCanvas** 将 AR 渲染移入 Web Worker，彻底不阻塞主线程
- 引入 **WebGL** 渲染替代 Canvas 2D，提升复杂光效渲染性能
- 实现检测频率动态调节（FPS 低时降低检测频率，优先保证渲染流畅）

### 7.3 分享与导出
- 截图功能：合并两层 Canvas 导出为 PNG
- 录制功能：使用 `MediaRecorder` 录制 AR 视频并下载
- 社交分享：一键生成带水印的视频片段
