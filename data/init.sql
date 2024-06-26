CREATE TABLE IF NOT EXISTS Users (
    user_id SERIAL PRIMARY KEY,
    full_name VARCHAR(255),
    role VARCHAR(50), -- host - manager
    user_name VARCHAR(255),
    password VARCHAR(255),
    user_nation VARCHAR(255),
    user_bday DATE,
    user_mail VARCHAR(255),
    show BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS Clubs (
    club_id INTEGER PRIMARY KEY not NULL SERIAL, 
    club_name VARCHAR(255),
	club_shortname VARCHAR(255), 
    total_player INTEGER,
    nation VARCHAR(255),
    manager INTEGER, -- Foreign key reference to Users
    show BOOLEAN DEFAULT TRUE,
    logo_low VARCHAR(255),
    logo_high VARCHAR(255),
    FOREIGN KEY (manager) REFERENCES Users(user_id)
);

CREATE TABLE IF NOT EXISTS Players (
    player_id INTEGER PRIMARY KEY not NULL SERIAL,
    player_name VARCHAR(255),
    player_bday DATE,
    player_club INTEGER, -- Foreign key reference to Club
    player_pos VARCHAR(50),
    player_nation VARCHAR(255),
    js_number INTEGER,
    show BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (player_club) REFERENCES Clubs(club_id)
);

CREATE TABLE IF NOT EXISTS Ranking (
    club_id INTEGER PRIMARY KEY,
    club_ranking INTEGER,
    club_points INTEGER,
    club_win INTEGER,
    club_draw INTEGER,
    club_lost INTEGER,
    club_goals INTEGER,
    club_gconcede INTEGER,
    club_gdif INTEGER,
    FOREIGN KEY (club_id) REFERENCES Clubs(club_id)
);

CREATE TABLE IF NOT EXISTS Referees (
    ref_id INTEGER PRIMARY KEY,
    ref_name VARCHAR(255),
    ref_birthd TIMESTAMP,
    ref_nation VARCHAR(255),
    ref_mail VARCHAR(255),
    show BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS Matches (
    match_id INTEGER PRIMARY KEY,
    team1 INTEGER, -- Foreign key reference to Club
    team2 INTEGER, -- Foreign key reference to Club
    start TIMESTAMP, -- YYYY:MM:DD HH:MM:SS
    finish TIMESTAMP,
    -- result VARCHAR(255),
    goal1 INTEGER,
    goal2 INTEGER,
    ref_id INTEGER, -- Foreign key reference to Referee
    var_id INTEGER, -- Foreign key reference to Referee
    lineman_id INTEGER, -- Foreign key reference to Referee
    show BOOLEAN DEFAULT TRUE,

    FOREIGN KEY (team1) REFERENCES Clubs(club_id),
    FOREIGN KEY (team2) REFERENCES Clubs(club_id),
    FOREIGN KEY (ref_id) REFERENCES Referees(ref_id),
    FOREIGN KEY (var_id) REFERENCES Referees(ref_id),
    FOREIGN KEY (lineman_id) REFERENCES Referees(ref_id)
);

CREATE TABLE IF NOT EXISTS Events (
    match_id INTEGER, -- Foreign key reference to Matches
    events VARCHAR(255),
    minute_event TIME,
    player_id INTEGER, -- Foreign key reference to Player
    PRIMARY KEY (match_id, events, minute_event),
    FOREIGN KEY (match_id) REFERENCES Matches(match_id),
    FOREIGN KEY (player_id) REFERENCES Players(player_id),
    show BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS Params (
    -- event_type VARCHAR(255),

    min_player_age INTEGER,
    max_player_age INTEGER,
    min_club_player INTEGER,
    max_club_player INTEGER,
    max_foreign_player INTEGER,

    points_win INTEGER,
    points_draw INTEGER,
    points_lose INTEGER,

    max_goal_types INTEGER,
    max_goal_time TIME
);

CREATE TABLE IF NOT EXISTS GoalTypes (
    type_id INTEGER PRIMARY KEY SERIAL,
    type_name VARCHAR(255)
)

-- default rule
INSERT INTO GoalTypes (type_name) VALUES ('A'), ('B'), ('C');
INSERT INTO Params (
    min_player_age,
    max_player_age,
    min_club_player,
    max_club_player,
    max_foreign_player,
    points_win,
    points_draw,
    points_lose,
    max_goal_types, 
    max_goal_time
) VALUES (
    16,
    40, 
    15, 
    22,
    3,
    2,
    1, 
    0,
    3, 
    '01:30:00'
)
