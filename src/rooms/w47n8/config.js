// W47N8 room config (separate from home W46N8; Misaki 2026-10-18 15:23). Positions verified on terrain.
module.exports = {
  ROOM: 'W47N8',
  SPAWN: [15, 18],
  // sources -> miner stand tile (his old containers at 26,11 and 11,43 are reused)
  SOURCES: [{ src: [27, 11], stand: [26, 11] }, { src: [11, 44], stand: [11, 43] }],
  CTL: [15, 25], CTL_CONT: [13, 26],
  // structures by RCL (cumulative). Compact block around spawn 15,18 on row 15-16 (open plain).
  BUILD: {
    2: { extension: [[13, 16], [14, 15], [16, 15], [17, 16], [12, 16]], container: [[13, 26]] },
    3: { extension: [[11, 16], [18, 16], [12, 15], [18, 15], [10, 16]], tower: [[14, 19]] },
    4: { extension: [[9, 16], [19, 16], [11, 15], [19, 15], [10, 15], [8, 16], [20, 15], [9, 15], [7, 16], [21, 15]], storage: [[16, 19]] },
  },
};
