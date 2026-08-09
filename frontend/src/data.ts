import type { Article, Language } from "./types";

export const articles: Article[] = [
  {
    id: "698123451",
    date: "2024-05-18",
    year: "2024",
    topic: "Options & Volatility",
    author: "Xuzhe (知乎 @徐哲)",
    url: "https://zhuanlan.zhihu.com/p/698123451",
    title: {
      en: "Understanding Option Volatility Skew in NVDA Earnings",
      zh: "从英伟达财报看期权波动率偏斜的套利机会",
      tw: "從英偉達財報看期權波動率偏斜的套利機會",
    },
    description: {
      en: "Exploring how market-neutral options positions capture implied volatility mispricing while dynamically hedging directional Delta exposure.",
      zh: "探索如何通过市场中性期权组合捕捉隐含波动率错配，同时动态对冲方向性 Delta 风险。",
      tw: "探索如何透過市場中性期權組合捕捉隱含波動率錯配，同時動態對沖方向性 Delta 風險。",
    },
    body: {
      en: "Understanding option pricing during earnings cycles requires comparing implied-volatility skew across call and put wings. Before opening either leg, the framework starts with the shape of the skew and its historical percentile.",
      zh: "理解财报季的期权定价，需要比较看涨与看跌翼部的隐含波动率偏斜。建立头寸前，首先观察偏斜的形状及其历史百分位。",
      tw: "理解財報季的期權定價，需要比較看漲與看跌翼部的隱含波動率偏斜。建立部位前，首先觀察偏斜的形狀及其歷史百分位。",
    },
    keyIdea: {
      en: "Implied-volatility skew reflects the asymmetry between panic and euphoria. A risk reversal can isolate that mispricing, but its convexity must be managed deliberately.",
      zh: "隐含波动率偏斜反映恐慌与狂热之间的不对称。Risk Reversal 可以提取这种错配，但必须主动管理其凸性风险。",
      tw: "隱含波動率偏斜反映恐慌與狂熱之間的不對稱。Risk Reversal 可以提取這種錯配，但必須主動管理其凸性風險。",
    },
  },
  {
    id: "682940129",
    date: "2024-02-10",
    year: "2024",
    topic: "Options & Volatility",
    author: "Xuzhe (知乎 @徐哲)",
    url: "https://zhuanlan.zhihu.com/p/682940129",
    title: {
      en: "Delta Neutral & Gamma Scalping in US Tech Stocks",
      zh: "Delta 中性与 Gamma 动态对冲：美股科技股实战",
      tw: "Delta 中性與 Gamma 動態對沖：美股科技股實戰",
    },
    description: {
      en: "A practical framework for converting realized movement into rebalancing cash flow while controlling option decay.",
      zh: "通过动态再平衡把实际波动转化为现金流，同时控制期权时间价值衰减。",
      tw: "透過動態再平衡把實際波動轉化為現金流，同時控制期權時間價值衰減。",
    },
    body: {
      en: "Delta-neutral positions benefit when price movement is large enough for repeated stock rebalancing to offset theta. The trade is not directionless: it exchanges directional exposure for path, volatility, and execution risk.",
      zh: "当价格波动足以让反复调仓收益抵消 Theta 时，Delta 中性头寸才可能获利。它并非没有风险，而是把方向风险换成路径、波动率与执行风险。",
      tw: "當價格波動足以讓反覆調倉收益抵消 Theta 時，Delta 中性部位才可能獲利。它並非沒有風險，而是把方向風險換成路徑、波動率與執行風險。",
    },
    keyIdea: {
      en: "Gamma scalping monetizes movement through disciplined rebalancing; profitability depends on realized volatility exceeding the volatility paid for.",
      zh: "Gamma Scalping 通过纪律性的再平衡变现波动；盈利取决于实际波动率是否超过买入期权时支付的波动率。",
      tw: "Gamma Scalping 透過紀律性的再平衡變現波動；獲利取決於實際波動率是否超過買入期權時支付的波動率。",
    },
  },
  {
    id: "665123984",
    date: "2023-11-04",
    year: "2023",
    topic: "US Macro & Fed Policy",
    author: "Xuzhe (知乎 @徐哲)",
    url: "https://zhuanlan.zhihu.com/p/665123984",
    title: {
      en: "Fed Rate Cycle & Macro Hedging Strategies",
      zh: "美联储利率周期下的宏观对冲与美股风险敞口",
      tw: "美聯儲利率週期下的宏觀對沖與美股風險曝險",
    },
    description: {
      en: "How rates, correlations, and the VIX term structure reshape portfolio hedges across market regimes.",
      zh: "利率、相关性与 VIX 期限结构如何在不同市场环境中重塑组合对冲。",
      tw: "利率、相關性與 VIX 期限結構如何在不同市場環境中重塑組合對沖。",
    },
    body: {
      en: "Rate-cycle changes alter both equity correlations and volatility term structure. Hedges should be selected for the scenario they protect, rather than treated as generic portfolio insurance.",
      zh: "利率周期变化会同时改变股票相关性与波动率期限结构。对冲工具应针对明确情景选择，而不是被当作通用的组合保险。",
      tw: "利率週期變化會同時改變股票相關性與波動率期限結構。對沖工具應針對明確情境選擇，而不是被當作通用的組合保險。",
    },
    keyIdea: {
      en: "Macro uncertainty is often better hedged with asymmetric option structures than with indiscriminate liquidation.",
      zh: "宏观不确定性通常更适合用非对称期权结构对冲，而不是不加区分地清仓。",
      tw: "宏觀不確定性通常更適合用非對稱期權結構對沖，而不是不加區分地清倉。",
    },
  },
  {
    id: "649201948",
    date: "2023-08-15",
    year: "2023",
    topic: "Tech Earnings & Hedging",
    author: "Xuzhe (知乎 @徐哲)",
    url: "https://zhuanlan.zhihu.com/p/649201948",
    title: {
      en: "Earnings IV Crush: Long Straddle vs Iron Condor",
      zh: "财报季 IV 崩塌陷阱：Long Straddle 与 Iron Condor",
      tw: "財報季 IV 崩塌陷阱：Long Straddle 與 Iron Condor",
    },
    description: {
      en: "Event volatility, post-announcement repricing, and the trade-offs between long and short premium structures.",
      zh: "事件波动率、公告后的重新定价，以及做多与做空权利金结构之间的取舍。",
      tw: "事件波動率、公告後的重新定價，以及做多與做空權利金結構之間的取捨。",
    },
    body: {
      en: "Implied volatility often rises before an earnings release and falls once binary uncertainty resolves. A correct directional forecast can still lose money when the option premium paid exceeds the realized move.",
      zh: "隐含波动率通常在财报前上升，并在二元不确定性消失后回落。即使方向判断正确，只要支付的期权权利金超过实际波幅，交易仍可能亏损。",
      tw: "隱含波動率通常在財報前上升，並在二元不確定性消失後回落。即使方向判斷正確，只要支付的期權權利金超過實際波幅，交易仍可能虧損。",
    },
    keyIdea: {
      en: "Do not carry an unhedged long straddle into earnings unless the implied move materially underprices your evidence-based range of outcomes.",
      zh: "除非隐含波幅显著低估了有证据支持的结果区间，否则不要持有未对冲的 Long Straddle 跨越财报。",
      tw: "除非隱含波幅顯著低估了有證據支持的結果區間，否則不要持有未對沖的 Long Straddle 跨越財報。",
    },
  },
  {
    id: "573019234",
    date: "2022-10-20",
    year: "2022",
    topic: "Portfolio Convexity",
    author: "Xuzhe (知乎 @徐哲)",
    url: "https://zhuanlan.zhihu.com/p/573019234",
    title: {
      en: "Positive Convexity in Portfolio Tail Risk Protection",
      zh: "尾部风险对冲：正凸性防暴跌指南",
      tw: "尾部風險對沖：正凸性防暴跌指南",
    },
    description: {
      en: "Designing tail-risk protection that grows as markets move further from ordinary conditions.",
      zh: "设计随市场偏离常态而加速增值的尾部风险保护。",
      tw: "設計隨市場偏離常態而加速增值的尾部風險保護。",
    },
    body: {
      en: "Out-of-the-money put spreads can add convexity while bounding premium cost. Position sizing still matters: protection that is too expensive can erode the portfolio before the tail event arrives.",
      zh: "虚值看跌价差可以在限制权利金成本的同时增加凸性。但仓位规模仍然关键：过于昂贵的保护会在尾部事件发生前持续侵蚀组合。",
      tw: "虛值看跌價差可以在限制權利金成本的同時增加凸性。但部位規模仍然關鍵：過於昂貴的保護會在尾部事件發生前持續侵蝕組合。",
    },
    keyIdea: {
      en: "Positive convexity can turn extreme moves into liquidity, provided the recurring cost is survivable.",
      zh: "只要持续成本可承受，正凸性就能把极端行情转化为流动性。",
      tw: "只要持續成本可承受，正凸性就能把極端行情轉化為流動性。",
    },
  },
];

export const uiCopy: Record<Language, Record<string, string>> = {
  en: {
    ask: "Ask Xuzhe's Notes",
    search: "Search articles in Chinese or English…",
    source: "Zhihu Source",
    drawerTitle: "Ask Xuzhe's Notes",
    drawerSubtitle: "Answers grounded in Xuzhe's Zhihu articles, with citations",
    question: "Ask a question…",
  },
  zh: {
    ask: "提问 AI 笔记助手",
    search: "中英文搜索文章…",
    source: "知乎原文",
    drawerTitle: "提问徐哲交易笔记",
    drawerSubtitle: "基于知乎文章的检索回答，并附原文引用",
    question: "输入问题…",
  },
  tw: {
    ask: "提問 AI 筆記助手",
    search: "中英文搜尋文章…",
    source: "知乎原文",
    drawerTitle: "提問徐哲交易筆記",
    drawerSubtitle: "基於知乎文章的檢索回答，並附原文引用",
    question: "輸入問題…",
  },
};
