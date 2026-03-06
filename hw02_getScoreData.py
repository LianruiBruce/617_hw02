from datetime import datetime, timezone
import json
import math
import time

import pandas as pd
from nba_api.stats.endpoints import leaguedashplayerstats, shotchartdetail
from nba_api.stats.static import players, teams


TARGET_PLAYERS = [
    "Walker Kessler",
    "Keyonte George",
    "Lauri Markkanen",
    "Jaren Jackson Jr.",
    "Ace Bailey",
]

ZONE_ORDER = [
    "At Rim",
    "Paint / Floater",
    "Midrange",
    "Corner 3",
    "Above Break 3",
]

DISTANCE_BINS = [
    (0, 4, "0-4 ft"),
    (5, 9, "5-9 ft"),
    (10, 14, "10-14 ft"),
    (15, 22, "15-22 ft"),
    (23, 50, "23+ ft"),
]


def get_current_nba_season(today=None):
    """按 NBA 赛季逻辑推断赛季字符串（如 2025-26）。"""
    now = today or datetime.now()
    start_year = now.year if now.month >= 10 else now.year - 1
    end_year_short = str(start_year + 1)[-2:]
    return f"{start_year}-{end_year_short}"


def write_data_asset(base_name, data, js_variable):
    with open(f"{base_name}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    with open(f"{base_name}.js", "w", encoding="utf-8") as f:
        f.write(f"window.{js_variable} = ")
        json.dump(data, f, ensure_ascii=False)
        f.write(";")


def classify_zone(row):
    x = abs(row["x"])
    y = row["y"]
    distance = row["distance"]
    shot_type = row["type"]

    if shot_type == "3PT Field Goal":
        if x >= 220 and y <= 92.5:
            return "Corner 3"
        return "Above Break 3"
    if distance <= 4:
        return "At Rim"
    if distance <= 14:
        return "Paint / Floater"
    return "Midrange"


def classify_action_bucket(action):
    action_lower = action.lower()

    if "pullup" in action_lower or "step back" in action_lower or "fadeaway" in action_lower:
        return "Self-Created Jumper"
    if "hook" in action_lower or "turnaround" in action_lower or "post" in action_lower:
        return "Post Touch"
    if "dunk" in action_lower or "layup" in action_lower or "tip" in action_lower or "alley oop" in action_lower:
        return "Paint Finish"
    if "driving" in action_lower or "floating" in action_lower or "running" in action_lower:
        return "Drive / Floater"
    if "jump shot" in action_lower or "catch and shoot" in action_lower:
        return "Spot-Up Jumper"
    return "Other"


def classify_distance_bucket(distance):
    for lower, upper, label in DISTANCE_BINS:
        if lower <= distance <= upper:
            return label
    return "23+ ft"


def normalize_metric(values_by_player):
    values = list(values_by_player.values())
    min_value = min(values)
    max_value = max(values)

    if math.isclose(min_value, max_value):
        return {player: 50.0 for player in values_by_player}

    return {
        player: round(((value - min_value) / (max_value - min_value)) * 100, 1)
        for player, value in values_by_player.items()
    }


def build_zone_summary(shot_df):
    grouped = (
        shot_df.groupby(["player", "zone"])
        .agg(attempts=("made", "size"), makes=("made", "sum"))
        .reset_index()
    )

    totals = shot_df.groupby("player").agg(total_attempts=("made", "size")).reset_index()
    summary = grouped.merge(totals, on="player", how="left")
    summary["fg_pct"] = (summary["makes"] / summary["attempts"]).fillna(0).round(3)
    summary["shot_share"] = (summary["attempts"] / summary["total_attempts"]).fillna(0).round(3)

    zone_records = summary.to_dict(orient="records")
    zone_records.sort(key=lambda item: (TARGET_PLAYERS.index(item["player"]), ZONE_ORDER.index(item["zone"])))
    return zone_records


def build_distance_summary(shot_df):
    grouped = (
        shot_df.groupby(["player", "distance_bucket"])
        .agg(attempts=("made", "size"), makes=("made", "sum"))
        .reset_index()
    )

    totals = shot_df.groupby("player").agg(total_attempts=("made", "size")).reset_index()
    summary = grouped.merge(totals, on="player", how="left")
    summary["fg_pct"] = (summary["makes"] / summary["attempts"]).fillna(0).round(3)
    summary["shot_share"] = (summary["attempts"] / summary["total_attempts"]).fillna(0).round(3)

    order = [label for _, _, label in DISTANCE_BINS]
    records = summary.to_dict(orient="records")
    records.sort(key=lambda item: (TARGET_PLAYERS.index(item["player"]), order.index(item["distance_bucket"])))
    return records


def build_action_summary(shot_df):
    grouped = (
        shot_df.groupby(["player", "action_bucket"])
        .agg(attempts=("made", "size"), makes=("made", "sum"))
        .reset_index()
    )

    totals = shot_df.groupby("player").agg(total_attempts=("made", "size")).reset_index()
    summary = grouped.merge(totals, on="player", how="left")
    summary["fg_pct"] = (summary["makes"] / summary["attempts"]).fillna(0).round(3)
    summary["shot_share"] = (summary["attempts"] / summary["total_attempts"]).fillna(0).round(3)
    summary = summary.sort_values(["player", "attempts"], ascending=[True, False])
    return summary.to_dict(orient="records")


def fetch_player_stats(season):
    response = leaguedashplayerstats.LeagueDashPlayerStats(
        season=season,
        season_type_all_star="Regular Season",
        per_mode_detailed="PerGame",
    )
    stats_df = response.get_data_frames()[0]
    stats_df = stats_df[stats_df["PLAYER_NAME"].isin(TARGET_PLAYERS)].copy()

    stats_df.rename(
        columns={
            "PLAYER_NAME": "player",
            "GP": "games",
            "MIN": "minutes",
            "PTS": "points",
            "REB": "rebounds",
            "AST": "assists",
            "FG3A": "threes_attempted",
            "FG3_PCT": "three_pct",
            "BLK": "blocks",
            "STL": "steals",
            "TOV": "turnovers",
            "PLUS_MINUS": "plus_minus",
        },
        inplace=True,
    )

    return stats_df[
        [
            "player",
            "games",
            "minutes",
            "points",
            "rebounds",
            "assists",
            "threes_attempted",
            "three_pct",
            "blocks",
            "steals",
            "turnovers",
            "plus_minus",
        ]
    ]


def build_story_summary(shot_df, stats_df):
    zone_lookup = {
        (item["player"], item["zone"]): item for item in build_zone_summary(shot_df)
    }
    action_lookup = {
        (item["player"], item["action_bucket"]): item for item in build_action_summary(shot_df)
    }
    shot_counts = shot_df.groupby("player").size().to_dict()

    role_raw_values = {
        "Floor spacing": {},
        "Rim pressure": {},
        "Shot creation": {},
        "Scoring load": {},
        "Rim protection proxy": {},
        "Shot versatility": {},
    }

    player_summaries = []
    for player in TARGET_PLAYERS:
        stats_row = stats_df[stats_df["player"] == player].iloc[0]
        total_shots = shot_counts.get(player, 0)
        at_rim_share = zone_lookup.get((player, "At Rim"), {}).get("shot_share", 0)
        paint_share = zone_lookup.get((player, "Paint / Floater"), {}).get("shot_share", 0)
        corner_share = zone_lookup.get((player, "Corner 3"), {}).get("shot_share", 0)
        above_break_share = zone_lookup.get((player, "Above Break 3"), {}).get("shot_share", 0)
        self_created_share = action_lookup.get((player, "Self-Created Jumper"), {}).get("shot_share", 0)
        drive_share = action_lookup.get((player, "Drive / Floater"), {}).get("shot_share", 0)
        spot_up_share = action_lookup.get((player, "Spot-Up Jumper"), {}).get("shot_share", 0)
        versatility = sum(
            1 for zone in ZONE_ORDER if zone_lookup.get((player, zone), {}).get("attempts", 0) >= 25
        )

        role_raw_values["Floor spacing"][player] = float(stats_row["threes_attempted"]) * (0.65 + float(stats_row["three_pct"]))
        role_raw_values["Rim pressure"][player] = (at_rim_share * 100) + (paint_share * 30)
        role_raw_values["Shot creation"][player] = float(stats_row["assists"]) + (self_created_share * 20) + (drive_share * 12)
        role_raw_values["Scoring load"][player] = float(stats_row["points"])
        role_raw_values["Rim protection proxy"][player] = float(stats_row["blocks"])
        role_raw_values["Shot versatility"][player] = versatility + (spot_up_share * 2) + (above_break_share * 2)

        player_summaries.append(
            {
                "player": player,
                "games": int(stats_row["games"]),
                "minutes": round(float(stats_row["minutes"]), 1),
                "points": round(float(stats_row["points"]), 1),
                "rebounds": round(float(stats_row["rebounds"]), 1),
                "assists": round(float(stats_row["assists"]), 1),
                "threes_attempted": round(float(stats_row["threes_attempted"]), 1),
                "three_pct": round(float(stats_row["three_pct"]), 3),
                "blocks": round(float(stats_row["blocks"]), 1),
                "steals": round(float(stats_row["steals"]), 1),
                "turnovers": round(float(stats_row["turnovers"]), 1),
                "plus_minus": round(float(stats_row["plus_minus"]), 1),
                "shot_records": int(total_shots),
            }
        )

    role_metrics = []
    for metric, values_by_player in role_raw_values.items():
        scores = normalize_metric(values_by_player)
        if metric == "Floor spacing":
            focus_zones = ["Corner 3", "Above Break 3"]
            description = "三分产量与命中率的组合代理。"
        elif metric == "Rim pressure":
            focus_zones = ["At Rim", "Paint / Floater"]
            description = "靠近篮筐与短距离区域的出手占比代理。"
        elif metric == "Shot creation":
            focus_zones = ["Paint / Floater", "Midrange", "Above Break 3"]
            description = "助攻与自创跳投/突破占比的组合代理。"
        elif metric == "Scoring load":
            focus_zones = ZONE_ORDER
            description = "赛季场均得分，表示进攻负荷。"
        elif metric == "Rim protection proxy":
            focus_zones = ["At Rim"]
            description = "用场均盖帽作为护框代理，属于防守端近似指标。"
        else:
            focus_zones = ZONE_ORDER
            description = "覆盖多个区域并保持一定投射占比的能力代理。"

        for player in TARGET_PLAYERS:
            role_metrics.append(
                {
                    "player": player,
                    "metric": metric,
                    "raw_value": round(values_by_player[player], 3),
                    "score": scores[player],
                    "focus_zones": focus_zones,
                    "description": description,
                }
            )

    assists_total = sum(item["assists"] for item in player_summaries)
    threes_total = sum(item["threes_attempted"] for item in player_summaries)
    shot_total = sum(item["shot_records"] for item in player_summaries)

    risk_cards = [
        {
            "id": "sample-size",
            "title": "Two frontcourt pieces still carry tiny samples",
            "subtitle": "Shot-chart attempts logged this season",
            "metric_label": "logged shots",
            "items": [
                {"player": item["player"], "value": item["shot_records"]}
                for item in player_summaries
            ],
            "narrative": "Kessler and JJJ have far fewer logged shots than George, Markkanen, and Bailey. Any clean spacing story should be treated as provisional.",
        },
        {
            "id": "creation-burden",
            "title": "Creation still leans toward George",
            "subtitle": "Assists per game among the projected starters",
            "metric_label": "assists per game",
            "items": [
                {"player": item["player"], "value": item["assists"]}
                for item in player_summaries
            ],
            "narrative": f"George accounts for {round((next(item['assists'] for item in player_summaries if item['player'] == 'Keyonte George') / assists_total) * 100, 1)}% of this five-man group's assists, which keeps the ball-handling hierarchy narrow.",
        },
        {
            "id": "spacing-load",
            "title": "Volume spacing depends on two players most",
            "subtitle": "Three-point attempts per game among the projected starters",
            "metric_label": "3PA per game",
            "items": [
                {"player": item["player"], "value": item["threes_attempted"]}
                for item in player_summaries
            ],
            "narrative": f"Markkanen and George produce {round(((next(item['threes_attempted'] for item in player_summaries if item['player'] == 'Lauri Markkanen') + next(item['threes_attempted'] for item in player_summaries if item['player'] == 'Keyonte George')) / threes_total) * 100, 1)}% of this lineup's three-point volume.",
        },
    ]

    return {
        "player_summaries": player_summaries,
        "zone_summary": build_zone_summary(shot_df),
        "distance_summary": build_distance_summary(shot_df),
        "action_summary": build_action_summary(shot_df),
        "role_metrics": role_metrics,
        "risk_cards": risk_cards,
        "method_notes": [
            "Role matrix values are proxies built from shot locations plus season per-game stats.",
            "Rim protection is approximated with blocks per game, because the current story does not collect full defensive tracking data.",
            "Sample size differs sharply across players, so small-sample interpretations should stay tentative.",
        ],
        "totals": {
            "shot_records": int(shot_total),
            "players": len(TARGET_PLAYERS),
        },
    }


def fetch_jazz_starting_five_shot_data():
    print("正在获取球队和球员基础信息...")

    jazz = [team for team in teams.get_teams() if team["abbreviation"] == "UTA"][0]
    jazz_id = jazz["id"]

    player_ids = {}
    for name in TARGET_PLAYERS:
        matches = players.find_players_by_full_name(name)
        if not matches:
            print(f"[警告] 未找到球员：{name}，将跳过。")
            continue
        player_ids[name] = matches[0]["id"]

    season = get_current_nba_season()
    print(f"本次抓取赛季: {season}")

    print("开始抓取投篮坐标数据（为避免 API 限流，每次请求暂停 1 秒）...")
    all_shots = pd.DataFrame()
    player_record_counts = {}

    for name, p_id in player_ids.items():
        print(f"正在获取 {name} 的数据...")
        response = shotchartdetail.ShotChartDetail(
            team_id=jazz_id,
            player_id=p_id,
            context_measure_simple="FGA",
            season_nullable=season,
            season_type_all_star="Regular Season",
        )
        df = response.get_data_frames()[0]
        player_record_counts[name] = len(df)
        all_shots = pd.concat([all_shots, df], ignore_index=True)
        time.sleep(1)

    print(f"抓取完成！共获取 {len(all_shots)} 条投篮记录。")

    shot_df = all_shots[
        [
            "PLAYER_NAME",
            "LOC_X",
            "LOC_Y",
            "SHOT_MADE_FLAG",
            "SHOT_TYPE",
            "ACTION_TYPE",
            "SHOT_DISTANCE",
        ]
    ].copy()

    shot_df.rename(
        columns={
            "PLAYER_NAME": "player",
            "LOC_X": "x",
            "LOC_Y": "y",
            "SHOT_MADE_FLAG": "made",
            "SHOT_TYPE": "type",
            "ACTION_TYPE": "action",
            "SHOT_DISTANCE": "distance",
        },
        inplace=True,
    )

    shot_df["zone"] = shot_df.apply(classify_zone, axis=1)
    shot_df["action_bucket"] = shot_df["action"].apply(classify_action_bucket)
    shot_df["distance_bucket"] = shot_df["distance"].apply(classify_distance_bucket)

    shot_records = shot_df.to_dict(orient="records")
    write_data_asset("jazz_shots_data", shot_records, "JAZZ_SHOT_DATA")
    print("投篮明细数据已保存到 jazz_shots_data.(json|js)")

    meta = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "season": season,
        "team_abbreviation": "UTA",
        "players_expected": TARGET_PLAYERS,
        "players_fetched": list(player_ids.keys()),
        "records_by_player": player_record_counts,
        "records_total": int(len(shot_df)),
        "source": "NBA Stats via nba_api (ShotChartDetail, LeagueDashPlayerStats)",
    }
    write_data_asset("jazz_shots_meta", meta, "JAZZ_SHOT_META")
    print("元数据已保存到 jazz_shots_meta.(json|js)")

    stats_df = fetch_player_stats(season)
    story_summary = build_story_summary(shot_df, stats_df)
    write_data_asset("jazz_story_summary", story_summary, "JAZZ_STORY_SUMMARY")
    print("叙事汇总数据已保存到 jazz_story_summary.(json|js)")


if __name__ == "__main__":
    fetch_jazz_starting_five_shot_data()