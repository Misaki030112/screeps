<template>
  <figure class="plate">
    <p class="kicker">两把尺，不是一根滑杆</p>
    <div class="doors">
      <div>
        <p class="door-name">家</p>
        <ul class="stick">
          <li>
            <strong>RCL8 · 升级目标 0</strong>
            <span>输能开着时不养常设升级工。掉级计时低于 100000 才留 1 只。外送从存储 20000 起，留下不低于 18000。</span>
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
            <span>reserveE。数字没变，仍是防御和孵化的垫。外送不从这里起。</span>
          </li>
        </ul>
      </div>
      <div>
        <p class="door-name">W47</p>
        <ul class="stick">
          <li>
            <strong>30000 / 20000 · 升级闩</strong>
            <span>连续 300 tick 不低于 30000，目标从 2 到 3。低于 20000 回到 2。威胁时仍是 2。</span>
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
      家的 20000 在 RCL8 以前是第三只的进入线，也和 boost 要留下的底撞在一起。RCL8 之后同一数字是外送的起步线，第三只那道闩不再被问。W47 的 20000 仍是节流松开，也是升级闩的退出线。两道 15000 数字相同，管的事不同。家在地板下面还有一条缩到一只的滞后，14500 进入、17550 离开，写在正文里。
    </figcaption>
  </figure>
</template>
