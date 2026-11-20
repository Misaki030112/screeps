<template>
  <figure class="plate">
    <p class="kicker">同一个键，三道读法</p>
    <ul class="stick">
      <li>
        <strong>女王的地板 · 缺键当作 0</strong>
        <span><code>walls.defReserve()</code> 是 <code>reserveE</code>，否则 0。台阶停住时，地板可以落到 base。没停时还要加上墙上的基金，并且仍然不低于这个储备。</span>
      </li>
      <li>
        <strong>整理终端 · 缺键当作 15000</strong>
        <span>搬运工的 <code>termPark</code> 用 <code>reserveE</code>，否则 15000。存储能量低于它，不开始把矿物在终端和存储之间挪。不搬能量。</span>
      </li>
      <li>
        <strong>矿物新趟，以及先存银行 · 缺键时不拦</strong>
        <span><code>walls.defLow</code> 在储备为 0 时是假。键不在，就不会因此停掉新的矿物趟，也不会把存储排到控制器容器前面。</span>
      </li>
    </ul>
    <figcaption>
      殖民地把 <code>Memory.defense.reserveE</code> 设在 15000 时，三道会在同一条水位上一起动。键不在，或写成 0，它们就散开：女王的地板落到 base，整理终端仍守 15000，矿物新趟和「先存银行」都不因此让路。升级工怎么用女王的地板，见<a href="/mechanisms/upgrade">升级页</a>。
    </figcaption>
  </figure>
</template>
