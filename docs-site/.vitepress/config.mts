import { defineConfig } from 'vitepress'

/** Index and query share one tokenizer so Chinese phrases match without a segmenter. */
function tokenize(text: string): string[] {
  const out: string[] = []
  let latin = ''
  let han: string[] = []
  const flushLatin = () => {
    if (!latin) return
    out.push(latin)
    latin = ''
  }
  const flushHan = () => {
    if (!han.length) return
    for (const c of han) out.push(c)
    for (let i = 0; i < han.length - 1; i++) out.push(han[i] + han[i + 1])
    han = []
  }
  for (const ch of text.toLowerCase()) {
    if (/[\u3400-\u9fff]/.test(ch)) {
      flushLatin()
      han.push(ch)
    } else if (/[a-z0-9]/.test(ch)) {
      flushHan()
      latin += ch
    } else {
      flushLatin()
      flushHan()
    }
  }
  flushLatin()
  flushHan()
  return out
}

const mechanisms = [
  { text: '主循环与 CPU', link: '/mechanisms/loop' },
  { text: '指挥官接管', link: '/mechanisms/commander' },
  { text: '孵化与身体', link: '/mechanisms/spawn' },
  { text: '搬运与能量', link: '/mechanisms/haul' },
  { text: '移动与寻路', link: '/mechanisms/move' },
  { text: '布局与印章', link: '/mechanisms/layout' },
  { text: '升级、地板与 softCap', link: '/mechanisms/upgrade' },
  { text: '防御与威胁', link: '/mechanisms/defense' },
  { text: '实验室与 boost', link: '/mechanisms/labs' },
  { text: '矿物与终端', link: '/mechanisms/minerals' },
  { text: 'Link 与枢纽', link: '/mechanisms/links' },
  { text: '外矿与预定', link: '/mechanisms/remotes' },
  { text: '部署', link: '/mechanisms/deploy' },
]

export default defineConfig({
  title: '殖民地手册',
  description: 'Misaki 在 Screeps shard3 上的殖民地：W46N8、W47N8，以及现在真正在跑的机制。',
  lang: 'zh-CN',
  // Editor notes stay in the repo. They are not a page.
  srcExclude: ['**/EDITORIAL_BACKLOG.md'],
  cleanUrls: true,
  lastUpdated: false,
  appearance: true,
  head: [
    ['link', { rel: 'icon', href: '/mark.svg' }],
    ['link', { rel: 'preconnect', href: 'https://fonts.googleapis.com' }],
    ['link', { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' }],
    ['link', {
      rel: 'stylesheet',
      href: 'https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700&family=Noto+Serif+SC:wght@500;600&display=swap',
    }],
    ['meta', { name: 'theme-color', content: '#f3efe6', media: '(prefers-color-scheme: light)' }],
    ['meta', { name: 'theme-color', content: '#141210', media: '(prefers-color-scheme: dark)' }],
  ],
  themeConfig: {
    logo: { light: '/mark.svg', dark: '/mark-dark.svg' },
    siteTitle: '殖民地手册',
    outline: { label: '本页', level: [2, 3] },
    docFooter: { prev: '上一篇', next: '下一篇' },
    darkModeSwitchLabel: '外观',
    lightModeSwitchTitle: '切换到浅色',
    darkModeSwitchTitle: '切换到深色',
    sidebarMenuLabel: '目录',
    returnToTopLabel: '回到顶部',
    externalLinkIcon: true,
    nav: [
      { text: '现状', link: '/now' },
      { text: '规划', link: '/plan' },
      { text: '机制', items: mechanisms },
      { text: '房间', link: '/reference/rooms' },
    ],
    sidebar: [
      {
        text: '读这本手册',
        items: [
          { text: '导读', link: '/' },
          { text: '现状', link: '/now' },
          { text: '规划', link: '/plan' },
        ],
      },
      { text: '机制', items: mechanisms },
      {
        text: '速查',
        items: [{ text: '房间与常数', link: '/reference/rooms' }],
      },
    ],
    footer: {
      message: 'shard3 · W46N8 · 依据仓库 src/ 写成',
      copyright: 'Misaki 的殖民地手册',
    },
    search: {
      provider: 'local',
      options: {
        locales: {
          root: {
            translations: {
              button: { buttonText: '搜索', buttonAriaLabel: '搜索手册' },
              modal: {
                noResultsText: '没有匹配的段落',
                resetButtonTitle: '清除',
                footer: {
                  selectText: '打开',
                  navigateText: '上下',
                  closeText: '关闭',
                },
              },
            },
          },
        },
        miniSearch: {
          options: { tokenize },
          searchOptions: {
            tokenize,
            combineWith: 'AND',
            prefix: true,
            fuzzy: false,
          },
        },
      },
    },
  },
})
