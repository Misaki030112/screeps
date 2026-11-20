<template>
  <figure class="plate">
    <p class="kicker">绕这一趟，要还剩得下</p>
    <div class="salv-board" aria-hidden="true">
      <div class="salv-walk">
        <div class="salv-who">人</div>
        <div class="salv-lane">
          <div class="lane-row">
            <span>能量</span>
            <span class="track"><i class="bar energy"><b>25</b></i></span>
          </div>
          <div class="lane-row">
            <span>矿物</span>
            <span class="track"><i class="bar loot"><b>49</b></i></span>
          </div>
        </div>
        <div class="salv-halo">
          <em>5</em>
          <div class="salv-pile">堆</div>
        </div>
      </div>
    </div>
    <ul class="legend">
      <li><i class="lg-now"></i>只有能量，最远 25。地上的还要扣衰减</li>
      <li><i class="lg-done"></i>存储还收得下，堆里有别的，最远 49</li>
      <li><i class="lg-halt"></i>堆的周围 5 格里有武装，不进新的候选</li>
    </ul>
    <div class="doors">
      <div>
        <p class="door-name">先减，再比</p>
        <ul class="stick">
          <li>
            <strong>剩下不少于 50</strong>
            <span>先扣别人占去的空位。地上的掉落再扣路上的衰减。墓碑和废墟不扣这一项。</span>
          </li>
          <li>
            <strong>拿到手的要盖过路程</strong>
            <span>这一只装得下的部分，不少于 50，再加每远一格 8。装不下的不算进这一趟。</span>
          </li>
        </ul>
      </div>
      <div>
        <p class="door-name">过了线才排先后</p>
        <ul class="stick">
          <li>
            <strong>矿物多 1000 分</strong>
            <span>加在已经过线的堆上，让它排在同样一载的能量前面。一小撮矿物不会因此值得走。</span>
          </li>
          <li>
            <strong>五格只挡新的堆</strong>
            <span>同一间房里，攻击或远程的部件还活着。已经认下的，不重新量这五格。</span>
          </li>
        </ul>
      </div>
    </div>
    <figcaption>
      两条横条是最远能看多远，不是已经拿到的分数。能量停在 25。家里的存储空位多于 1000、堆里又有矿物或强化物，才把横条放到 49，每个单位按 5 点能量计。衰减是当量除以 1000 向上取整，再乘格数，而且只对地上的掉落。虚线圈着堆：武装在这 5 格里，这堆就不进新的候选。
    </figcaption>
  </figure>
</template>
