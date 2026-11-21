import DefaultTheme from 'vitepress/theme'
import Layout from './Layout.vue'
import './custom.css'
import ArchDiagram from './components/ArchDiagram.vue'
import CpuOrder from './components/CpuOrder.vue'
import FlowDiagram from './components/FlowDiagram.vue'
import RoadmapDiagram from './components/RoadmapDiagram.vue'
import SpawnQueue from './components/SpawnQueue.vue'
import UpgradeFloors from './components/UpgradeFloors.vue'
import HaulOrder from './components/HaulOrder.vue'
import HaulReads from './components/HaulReads.vue'
import ThreatFsm from './components/ThreatFsm.vue'
import DefenseEnergy from './components/DefenseEnergy.vue'
import RampHold from './components/RampHold.vue'
import DeployPath from './components/DeployPath.vue'
import UnstuckLadder from './components/UnstuckLadder.vue'
import HubYield from './components/HubYield.vue'
import HomeStamps from './components/HomeStamps.vue'
import HubCore from './components/HubCore.vue'
import LabGates from './components/LabGates.vue'
import LinkFlow from './components/LinkFlow.vue'
import BuildYield from './components/BuildYield.vue'
import SalvageScore from './components/SalvageScore.vue'
import ColonyStrip from './components/ColonyStrip.vue'
import CmdTick from './components/CmdTick.vue'
import CmdLife from './components/CmdLife.vue'
import RemoteLines from './components/RemoteLines.vue'

export default {
  extends: DefaultTheme,
  Layout,
  enhanceApp({ app }) {
    app.component('ArchDiagram', ArchDiagram)
    app.component('CpuOrder', CpuOrder)
    app.component('FlowDiagram', FlowDiagram)
    app.component('RoadmapDiagram', RoadmapDiagram)
    app.component('SpawnQueue', SpawnQueue)
    app.component('UpgradeFloors', UpgradeFloors)
    app.component('HaulOrder', HaulOrder)
    app.component('HaulReads', HaulReads)
    app.component('ThreatFsm', ThreatFsm)
    app.component('DefenseEnergy', DefenseEnergy)
    app.component('RampHold', RampHold)
    app.component('DeployPath', DeployPath)
    app.component('UnstuckLadder', UnstuckLadder)
    app.component('HubYield', HubYield)
    app.component('HomeStamps', HomeStamps)
    app.component('HubCore', HubCore)
    app.component('LabGates', LabGates)
    app.component('LinkFlow', LinkFlow)
    app.component('BuildYield', BuildYield)
    app.component('SalvageScore', SalvageScore)
    app.component('ColonyStrip', ColonyStrip)
    app.component('CmdTick', CmdTick)
    app.component('CmdLife', CmdLife)
    app.component('RemoteLines', RemoteLines)
  },
}
