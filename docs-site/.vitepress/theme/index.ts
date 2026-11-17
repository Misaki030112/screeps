import DefaultTheme from 'vitepress/theme'
import Layout from './Layout.vue'
import './custom.css'
import ArchDiagram from './components/ArchDiagram.vue'
import FlowDiagram from './components/FlowDiagram.vue'
import RoadmapDiagram from './components/RoadmapDiagram.vue'
import SpawnQueue from './components/SpawnQueue.vue'
import UpgradeFloors from './components/UpgradeFloors.vue'
import HaulOrder from './components/HaulOrder.vue'
import HaulReads from './components/HaulReads.vue'
import ThreatFsm from './components/ThreatFsm.vue'
import DefenseEnergy from './components/DefenseEnergy.vue'
import LabGates from './components/LabGates.vue'
import ColonyStrip from './components/ColonyStrip.vue'

export default {
  extends: DefaultTheme,
  Layout,
  enhanceApp({ app }) {
    app.component('ArchDiagram', ArchDiagram)
    app.component('FlowDiagram', FlowDiagram)
    app.component('RoadmapDiagram', RoadmapDiagram)
    app.component('SpawnQueue', SpawnQueue)
    app.component('UpgradeFloors', UpgradeFloors)
    app.component('HaulOrder', HaulOrder)
    app.component('HaulReads', HaulReads)
    app.component('ThreatFsm', ThreatFsm)
    app.component('DefenseEnergy', DefenseEnergy)
    app.component('LabGates', LabGates)
    app.component('ColonyStrip', ColonyStrip)
  },
}
