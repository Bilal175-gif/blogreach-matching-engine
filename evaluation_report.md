# BlogReach Matching Engine - Evaluation Report

Scenarios: 20 (manually judged, see `test_scenarios.csv`).
Dataset: 44 publishers (42 active) from `data/publishers.csv` (synthetic).

## Summary

- **Top-1 accuracy: 100%** (20/20)
- **Top-3 hit rate: 100%** (20/20)

## Per-scenario results

| Scenario | Advertiser | Expected | Engine #1 | Engine top-3 | Top-1 | Top-3 |
|---|---|---|---|---|---|---|
| S01 | PhoneHub.pk (mobile retailer) | tech-01 | tech-01 | tech-01;tech-03;tech-05 | yes | yes |
| S02 | DesiSpice Foods | food-02 | food-02 | food-02;life-03;travel-03 | yes | yes |
| S03 | InvestSmart App | fin-02 | fin-02 | fin-02;fin-01;fin-04 | yes | yes |
| S04 | FitFuel Supplements | health-01 | health-01 | health-01;health-03;food-01 | yes | yes |
| S05 | Northern Trails Co | travel-03 | travel-03 | travel-03;food-02;life-03 | yes | yes |
| S06 | PixelForge Games | game-01 | game-01 | game-01;game-02;tech-01 | yes | yes |
| S07 | VelvetWardrobe | fashion-01 | fashion-01 | fashion-01;fashion-02;life-02 | yes | yes |
| S08 | LearnLoop | edu-02 | edu-02 | edu-02;edu-01;edu-03 | yes | yes |
| S09 | FoundersFund | biz-01 | biz-01 | biz-01;biz-02;tech-02 | yes | yes |
| S10 | CricBet Sports | sports-01 | sports-01 | sports-01;tech-01;life-02 | yes | yes |
| S11 | GharNeeds | home-01 | home-01 | home-01;life-03;life-01 | yes | yes |
| S12 | Nestlings | life-03 | life-03 | life-03;life-01;food-02 | yes | yes |
| S13 | TechBazaar | tech-07 | tech-07 | tech-07;edu-01;health-01 | yes | yes |
| S14 | HalalWealth | fin-05 | fin-05 | fin-05;fin-03;biz-02 | yes | yes |
| S15 | NutriBox | food-04 | food-04 | food-04;food-03;health-02 | yes | yes |
| S16 | TinyStartup | NONE | - | - | yes | yes |
| S17 | RangRiwayat | fashion-02 | fashion-02 | fashion-02;fin-05;life-01 | yes | yes |
| S18 | PlayTech Arena | tech-04 | tech-04 | tech-04;game-03;tech-02 | yes | yes |
| S19 | LuxeEscapes | travel-04 | travel-04 | travel-04;travel-02;travel-01 | yes | yes |
| S20 | StudyBuddy | edu-03 | edu-03 | edu-03 | yes | yes |

## Analysis

All 20 scenarios matched the manually judged expectation at rank #1, including the no-match conflict scenario (S16), where the engine correctly returned zero publishers and raised a budget warning.

## Limitations

- The 20 scenarios were judged by the task author against the same synthetic dataset the engine scores, so this measures ranking consistency, not real-world precision.
- Real evaluation needs historical BlogReach campaign data (which briefs converted).
- Traffic/DA figures are synthetic; production should pull live Similarweb/Moz-style data.
