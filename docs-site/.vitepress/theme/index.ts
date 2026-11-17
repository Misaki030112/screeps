import DefaultTheme from 'vitepress/theme'
import Layout from './Layout.vue'
import './custom.css'
import ArchDiagram from './components/ArchDiagram.vue'
import FlowDiagram from './components/FlowDiagram.vue'
import RoadmapDiagram from './components/RoadmapDiagram.vue'
import ColonyStrip from './components/ColonyStrip.vue'

export default {
  extends: DefaultTheme,
  Layout,
  enhanceApp({ app }) {
    app.component('ArchDiagram', ArchDiagram)
    app.component('FlowDiagram', FlowDiagram)
    app.component('RoadmapDiagram', RoadmapDiagram)
    app.component('ColonyStrip', ColonyStrip)
  },
}
