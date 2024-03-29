CREATE TABLE presenters (pid INTEGER PRIMARY KEY, name VARCHAR);
CREATE TABLE talks (tid INTEGER PRIMARY KEY, name VARCHAR, description VARCHAR);
CREATE TABLE hours (hid INTEGER PRIMARY KEY, time DATETIME);
CREATE TABLE rooms (rid INTEGER PRIMARY KEY, name VARCHAR, max_bookings INTEGER);
CREATE TABLE gives_talk (pid INTEGER, tid INTEGER);
CREATE TABLE presenter_available (pid INTEGER, hid INTEGER);
CREATE TABLE talk_available (tid INTEGER, hid INTEGER);
CREATE TABLE room_available (rid INTEGER, hid INTEGER);
CREATE TABLE room_suitable_for (rid INTEGER, tid INTEGER);
CREATE TABLE attendee (aid INTEGER PRIMARY KEY);
CREATE TABLE attendee_interest (aid INTEGER, tid INTEGER);
CREATE TABLE schedule (pid INTEGER, tid INTEGER, hid INTEGER, rid INTEGER);
CREATE TABLE room_class_member(rrid INTEGER PRIMARY KEY, name VARCHAR);
CREATE TABLE room_class_members(rid INTEGER, rrid INTEGER);