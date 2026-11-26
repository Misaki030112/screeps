<template>
  <figure class="plate">
    <p class="kicker">两把尺，不是一根滑杆</p>
    <div class="doors">
      <div>
        <p class="door-name">家</p>
        <ul class="stick">
          <li>
            <strong>RCL8 · 升级目标 1</strong>
            <span>一只，身体最多 15 WORK。不把能量送到 W47。两房各自升级。</span>
          </li>
          <li>
            <strong>20000 · 第三只进入</strong>
            <span>只在 RCL8 以前。地板再加 5000，容器的滑动平均不低于 1200，连续 300 tick。</span>
          </li>
          <li>
            <strong>18000 · 第三只离开</strong>
            <span>存储低于地板加 3000，或滑动平均低于 700。不必再等 300 tick。</span>
          </li>
          <li>
            <strong>15000 · 地板</strong>
            <span>reserveE。数字没变，仍是防御和孵化的垫。不把能量运到 W47。</span>
          </li>
        </ul>
      </div>
      <div>
        <p class="door-name">W47</p>
        <ul class="stick">
          <li>
            <strong>40000 / 30000 · 升级闩</strong>
            <span>连续 500 tick 不低于 40000，目标从 2 到 3。低于 30000 回到 2。威胁时仍是 2。</span>
          </li>
          <li>
            <strong>25000 / 22000 · 能量软顶</strong>
            <span>到 25000 清除，低于 22000 才再武装。不决定升级工只数。</span>
          </li>
          <li>
            <strong>20000 / 15000 · 节流</strong>
            <span>到 20000 松开。松开之后，要低于 15000 才重新合上。</span>
          </li>
        </ul>
      </div>
    </div>
    <figcaption>
      家的 20000 在 RCL8 以前是第三只的进入线。8 级的目标固定是 1 只，不再问这道闩。Boost 从存储取能量后留下的底现在是 5000，和这道 20000 不是同一个数。W47 的 20000 只是节流松开。升级闩是 40000 进、30000 出。两道 15000 数字相同，管的事不同。家在地板下面还有一条缩到一只的滞后，14500 进入、17550 离开，写在正文里。
    </figcaption>
  </figure>
</template>
