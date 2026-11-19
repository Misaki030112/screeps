<template>
  <figure class="plate">
    <p class="kicker">W47N8 核心这一角 · x 向右，y 向下</p>
    <div class="core">
      <div class="node stop c3231">
        <strong>32,31 延伸</strong>
        <span>口袋北面。</span>
      </div>
      <div class="node c3331">
        <strong>33,31 路</strong>
        <span>北侧出口。</span>
      </div>
      <div class="node later c3431">
        <strong>34,31 塔</strong>
        <span>顺序里的第四座。</span>
      </div>
      <div class="node c3531">
        <strong>35,31 路</strong>
        <span>通向存储。</span>
      </div>
      <div class="node c3232">
        <strong>32,32 平地</strong>
        <span>空着。不是路。</span>
      </div>
      <div class="node stop c3332">
        <strong>33,32 终端</strong>
        <span>建筑。</span>
      </div>
      <div class="node now c3432">
        <strong>34,32 岗位</strong>
        <span>路。filler 停在这里。</span>
      </div>
      <div class="node done c3532">
        <strong>35,32 存储</strong>
        <span>建筑。</span>
      </div>
      <div class="node stop c3233">
        <strong>32,33 link</strong>
        <span>枢纽 link。</span>
      </div>
      <div class="node c3333">
        <strong>33,33 容器</strong>
        <span>配置里的枢纽容器，也是路。</span>
      </div>
      <div class="node done c3433">
        <strong>34,33 核心</strong>
        <span>路。CORE。</span>
      </div>
      <div class="node stop c3234">
        <strong>32,34 延伸</strong>
        <span>link 南面。</span>
      </div>
      <div class="node c3334">
        <strong>33,34 路</strong>
        <span>旧 link 的格子。</span>
      </div>
      <div class="node stop c3335">
        <strong>33,35 塔</strong>
        <span>核心南边。</span>
      </div>
    </div>
    <ul class="legend">
      <li><i class="lg-now"></i>filler 的岗位</li>
      <li><i class="lg-done"></i>核心与存储</li>
      <li><i class="lg-later"></i>第四座塔，排在三座之后</li>
      <li><i class="lg-stop"></i>建筑，走不过</li>
    </ul>
    <figcaption>
      现在的出生点是 15,18，在西边。34,30 是以后放置顺序的第一格。33,34 是路。过路的代价见移动那一页。
    </figcaption>
  </figure>
</template>
