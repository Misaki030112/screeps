<template>
  <figure class="plate">
    <p class="kicker">一条指令的四种结局</p>
    <div class="gates">
      <div class="node now">
        <strong>还活着</strong>
        <span>自己的 on 为真。sticky 不看时钟。否则要时间还小于 until，或还小于 at 加 ttl。</span>
      </div>
      <div class="node later">
        <strong>停着</strong>
        <span>这一条的 on 写成 0。不算活，也不算过期。条目留在袋子里。打开整层不把它改回 1。</span>
      </div>
      <div class="node stop">
        <strong>整层关着</strong>
        <span>Memory.cmd.on 写成 0。袋子留着，这一拍不扫。再打开的当时不删。下一次清扫才拿走过期的。</span>
      </div>
      <div class="node done">
        <strong>拿掉</strong>
        <span>到点且整层开着，清扫时删。只问到一条已经过期的，也删。放开当时就删。开着却没有时钟的非粘性指令，同样删。</span>
      </div>
    </div>
    <figcaption>
      还活着、停着、整层关着，条目都在袋子里。写成 0 是停着。放开，或到了 until 那一拍并且整层还开着，才把条目拿掉。
    </figcaption>
  </figure>
</template>
