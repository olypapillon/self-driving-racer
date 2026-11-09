import benchmark

LEADERBOARD = {
    "trial_seeds": 5,
    "algorithms": [
        {"rank": 1, "name": "Fast", "family": "Learned", "trial_finished": "5/5",
         "trial_mean": 25.5, "trial_best": 25.25, "battle_avg_place": 1.5,
         "battle_wins": 9, "cpu_ms_per_race_second": 9.03},
        {"rank": 2, "name": "Shaky", "family": "Learned", "trial_finished": "4/5",
         "trial_mean": 27.0, "trial_best": 26.0, "battle_avg_place": 4,
         "battle_wins": 0, "cpu_ms_per_race_second": 8.0},
        {"rank": 3, "name": "Lost", "family": "Rules", "trial_finished": "0/5",
         "trial_mean": None, "trial_best": None, "battle_avg_place": 6,
         "battle_wins": 0, "cpu_ms_per_race_second": 2.0},
    ],
}


def test_table_rows_show_times_partial_finishes_and_dnf():
    table = benchmark.leaderboard_table(LEADERBOARD).splitlines()
    assert len(table) == 2 + 3
    assert table[2] == "| 1 | Fast | Learned | 25.50 s | 25.25 s | 1.50 | 9 | 9.0 |"
    assert "27.00 s (4/5 finished)" in table[3]
    assert "| DNF | - |" in table[4]


def test_only_the_text_between_the_markers_changes():
    readme = f"intro\n{benchmark.TABLE_START}\nold table\n{benchmark.TABLE_END}\noutro\n"
    updated = benchmark.with_table(readme, "new table")
    assert updated == f"intro\n{benchmark.TABLE_START}\nnew table\n{benchmark.TABLE_END}\noutro\n"
    assert benchmark.with_table(updated, "new table") == updated  # stable on rerun
