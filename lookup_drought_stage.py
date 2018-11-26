mo_data = {
    # mo: ds[1, 2, 3], r[1, 2, 3] ## ds=drought_stage, r=rescission
    1: ([.40, .30, .25], [.60, .50, .45]),
    2: ([.50, .35, .25], [.70, .55, .45]),
    3: ([.65, .45, .30], [.85, .55, .45]),
    4: ([.85, .60, .35], [1.0, .80, .55]),
    5: ([.75, .55, .35], [.95, .75, .55]),
    6: ([.65, .45, .30], [.85, .65, .50]),
    7: ([.55, .45, .25], [.75, .65, .50]),
    8: ([.50, .40, .25], [.70, .60, .45]),
    9: ([.45, .35, .25], [.65, .55, .45]),
    10: ([.40, .30, .25],[.60, .50, .45]),
    11: ([.35, .30, .25],[.55, .50, .45]),
    12: ([.35, .30, .25],[.55, .50, .45]),
}

drought_stages = {
    0: 1.00, # gallons per capita per day
    1: 0.85,
    2: 0.55,
    3: 0.40,
}