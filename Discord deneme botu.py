import discord
from discord.ext import commands

import sqlite3

bot = commands.Bot(command_prefix='!')

conn = sqlite3.connect('leaderboard.db')
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS leaderboard (team_id INTEGER PRIMARY KEY, team_points INTEGER)')

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

@bot.event
async def on_voice_state_update(member, before, after):
    if not after.channel:
        return

    if before.channel == after.channel:
        return

    if after.channel.members < 2:
        return

    team_id = hash(frozenset([member.id, after.channel.id]))

    c.execute('SELECT team_points FROM leaderboard WHERE team_id = ?', (team_id,))
    team_points = c.fetchone()

    if team_points:
        team_points = team_points[0]
    else:
        team_points = 0

    if after.channel.members == 2:
        team_points += 1

    c.execute('INSERT OR REPLACE INTO leaderboard VALUES (?, ?)', (team_id, team_points))
    conn.commit()

@bot.event
async def on_friend_request(from_user, to_user):
    c.execute('SELECT team_id FROM leaderboard WHERE team_id LIKE ?', (f'%{from_user.id}%',))
    team_id = c.fetchone()

    if team_id:
        return

    c.execute('SELECT team_id FROM leaderboard WHERE team_id LIKE ?', (f'%{to_user.id}%',))
    team_id = c.fetchone()

    if team_id:
        return

    team_id = hash(frozenset([from_user.id, to_user.id]))
    c.execute('INSERT INTO leaderboard VALUES (?, ?)', (team_id, 0))
    conn.commit()

@bot.command(name='leaderboard')
async def leaderboard(ctx):
    c.execute('SELECT team_id, team_points FROM leaderboard ORDER BY team_points DESC')

    leaderboard_str = 'LEADERBOARD\n'
    leaderboard_str += '-----------\n'

    for row in c.fetchall():
        team_id, team_points = row
        member1_id, member2_id = list(frozenset(hash(team_id)))

        member1 = bot.get_user(member1_id)
        member2 = bot.get_user(member2_id)

        leaderboard_str += f'{member1.name} and {member2.name}: {team_points} points\n'

    await ctx.send(leaderboard_str)

bot.run('YOUR_DISCORD_BOT_TOKEN')
