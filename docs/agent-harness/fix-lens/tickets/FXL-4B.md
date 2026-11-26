+++
key = "FXL-4B"
title = "Enum and field lookups must ignore JavaScript object built-ins"
rank = 5
blocked_by = ["FXL-4"]
labels = []
+++
A pasted enum value such as `constructor`, `toString` or `__proto__` must be treated as an unknown value. Today a
plain-object lookup can return a built-in from `Object.prototype` instead of `undefined` (FXL-4 review note F1).

Acceptance criteria
- AC0: A test imports `lookup` and `enumName` from `src/dictionary.js` and `decode` from `src/decode.js`.
- AC1: `enumName("FIX.4.4", 54, v)` returns `null` for each `v` in `constructor`, `toString`, `__proto__`,
  `hasOwnProperty`, `valueOf`.
- AC2: `lookup("FIX.4.4", t)` returns `null` for `t` = `"constructor"`, `"__proto__"`, `"toString"`.
- AC3: Decoding `8=FIX.4.4|9=35|35=0|34=1|49=A|56=B|54=constructor|10=240|` shows tag 54 with value
  `constructor`, `enumName` `unknown value`, and no field shows a function or `[object Object]`.
- AC4: Lookups check own keys only (`Object.hasOwn`, or a `Map`, or null-prototype objects). The generated JSON
  files don't change.
