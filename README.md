# news-image-20261121

[![make.fun · news-image-20261121](https://make.fun/badge/news-image-20261121.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![rank](https://make.fun/badge/news-image-20261121/bapenven-ctrl/news-image-20261121/rank.svg)](https://make.fun/bounty/news-image-20261121/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![reward](https://make.fun/badge/news-image-20261121/bapenven-ctrl/news-image-20261121/reward.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)

One page of world news for **Saturday 21 November 2026**: 35 stories, every one
of them reported that day, in at least one time zone.

## What is on the page

- **3 lead stories**, fully illustrated: COP31 ends Saturday with no deal in
  Antalya, three Houthi missiles shot down over Riyadh, and BepiColombo
  entering orbit around Mercury — only the second mission ever to do so.
- **10 illustrated cards**: the magnitude 6.7 earthquake in Peru, Air Niugini's
  emergency landing in Davao (146 safe), Australia's two-day Ashes win in
  Perth, the Russian cargo ship Sparta II hit by drones in the Gulf of
  Finland, KL Rahul's 136 in Wellington, Las Vegas qualifying (Antonelli
  fastest, Verstappen on pole), bitcoin's fall below $58,000, Russia's
  overnight missile-and-drone barrage on Ukraine, Iran's claim of downing a
  US drone over Hormuz, and the Israeli strike in Gaza City.
- **22 briefs**, a world map with pins for stories 1–13, and a printed
  **DATE CHECK** box listing the stories that were checked and deliberately
  *not* shown as Saturday's news (among them the Jurf al-Sakhar operation,
  the Texas execution and the Palisades verdict — all Friday's news — plus
  the COP31 deal, which was only announced Sunday). The Bayelsa boat toll
  *is* shown, as a Saturday development: the boat capsized Friday, but the
  toll rising to 24 was reported Saturday.

Every story was date-checked against a datelined source (UTC and local time)
before it was drawn; claims are labelled as claims on the page.

## Run it

```sh
python3 main.py  # copies entry.png into $MAKEFUN_OUTPUT_DIR (or /output)
```

`main.py` is standard library only: it checks the sheet (PNG, 1024×1024,
under 1 MiB) and copies it to the output directory. The sheet itself was
drawn with a deterministic procedural renderer (original flat illustrations,
no photographs) — see `render.py`, which writes the same `entry.png` when
run with Pillow installed.

## License

MIT — see `LICENSE`.
