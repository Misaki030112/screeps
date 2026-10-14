// Controller sign text (one constant), shared by upgrader (own room) and reserver (remote).
const SIGN = 'Peace grows here, guarded by steel. Cross in war, fall in silence.';
// true when ctl's sign is missing/different or not by `username`
const needs = (ctl, username) => !!ctl && (!ctl.sign || ctl.sign.text !== SIGN || ctl.sign.username !== username);
module.exports = { SIGN, needs };
