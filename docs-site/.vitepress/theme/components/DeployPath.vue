<template>
  <figure class="plate">
    <p class="kicker">从源码到游戏里的模块</p>
    <div class="arch-col">
      <div class="step">
        <span class="num">1</span>
        <div class="node">
          <strong>src 里的 js</strong>
          <span>按目录放着的源码。上传前先变成下一层的名字。</span>
        </div>
      </div>
      <div class="step">
        <span class="num">2</span>
        <div class="node">
          <strong>摊平进 dist</strong>
          <span>一层文件，斜杠换成点。相对 require 改成这些名字。对不上文件，构建就停。</span>
        </div>
      </div>
      <div class="step">
        <span class="num">3</span>
        <div class="node now">
          <strong>检查</strong>
          <span>语法，家的快照 600 tick，再按清单跑测试。任一步失败，上传不开始。</span>
        </div>
      </div>
      <div class="step">
        <span class="num">4</span>
        <div>
          <p class="fork-label">两条都先过检查</p>
          <div class="doors">
            <div class="node">
              <strong>upload.js</strong>
              <span>游戏分支默认叫 default。参数可以换成别的分支名。</span>
            </div>
            <div class="node done">
              <strong>deploy.py</strong>
              <span>永远传到 default。检查前拿一把锁，避免两次同时上传。</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    <figcaption>
      没过检查的模块，这两条路都不会传。
    </figcaption>
  </figure>
</template>
