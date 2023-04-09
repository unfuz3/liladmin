# LilAdmin's source code, by unfuz3.
# https://github.com/unfuz3/liladmin.git
# This discord bot, meant to be used in small servers, is a lightweight, light-functionality bot. It can be used to moderate servers in some aspects.
# Functions: Leveling system, welcoming and leaving.
# Under development.


### SETTINGS ###

# Importing libraries
# discord, sqlite3 must be downloaded from pip
import discord
import os
from dotenv import load_dotenv
import sqlite3
import datetime
from discord.ext import commands
import emoji

# Loads the env variables to read the bot's token
load_dotenv()

# Bot's client basic object and settings
client = commands.Bot(intents=discord.Intents.all(), command_prefix="!", help_command=commands.DefaultHelpCommand(no_category = 'Commands'))


### FUNCTIONS ###

# Mathematical functions to get the exp-level ratio
def expToLvl(exp):
	return int((exp/1000) ** (2/3))

def lvlToExp(lvl):
	return int(1000 * (lvl ** (3/2)))


# Check if user is in the server's database
def checkUser(msg):
	user = msg.author
	con, cur = sqlConnect(f"{msg.guild.id}.db")
	cur.execute(f"SELECT * FROM users WHERE id='{user.id}'")

	# If user wasn't in the database, insert the default values into it
	if (cur.fetchall() == []):
		print(f"[INFO] Adding user {user.name}#{user.discriminator} to the server {msg.guild.name} database.")
		cur.execute("INSERT INTO users (id,username,discriminator,level,exp,lastmsgtimestamp) VALUES (?,?,?,?,?,?)",(user.id,user.name,user.discriminator,0,0,msg.created_at.timestamp()))
		con.commit()
	
	con.close()


# Updates the exp and level from a user when he sends a message
def updateLvling(msg):
	user = msg.author
	currentDatetime = msg.created_at

	# Retrieve and calculate the time interval between messages
	con, cur = sqlConnect(f"{msg.guild.id}.db")
	cur.execute(f"SELECT level,exp,lastmsgtimestamp FROM users WHERE id='{user.id}'")
	level, exp, lastMsgTimeStamp = cur.fetchone()
	lastDatetime = datetime.datetime.fromtimestamp(lastMsgTimeStamp, datetime.timezone.utc)
	timeInterval = (currentDatetime - lastDatetime).seconds # The tzinfo makes the currentDatetime timezone-naive

	# Main exp sources, depends on the time interval since the last messsage from the same user
	if (timeInterval < 5):
		pass # no exp / spam (doesn't update the lastmsgtimestamp value)
	else:
		if (timeInterval <= 10):
			newExp = exp + 2 # low exp
		elif (timeInterval <= 60):
			newExp = exp + 10 # low exp
		elif (timeInterval <= 600):
			newExp = exp + 50 # low exp
		elif (timeInterval > 600):
			newExp = exp + 100 # low exp
		else:
			print(f"[WARN] Extreme case in exp rewarding, unusual behavior.")
		
		cur.execute(f"UPDATE users SET exp={newExp}, lastmsgtimestamp={(currentDatetime).timestamp()} WHERE id={user.id}")

		# Level updating
		expectedLevel = expToLvl(newExp)

		if (expectedLevel == (level + 1)):
			cur.execute(f"UPDATE users SET level={expectedLevel} WHERE id={user.id}")
		elif (expectedLevel == level):
			pass
		else:
			print(f"[WARN] Extreme case in level updating, unusual behavior.")
	
	cur.close()
	con.commit()
	con.close()


# Shortcut for getting connection and cursor object from a server's database
def sqlConnect(dbname:str) -> tuple[sqlite3.Connection, sqlite3.Cursor]:
	con = sqlite3.connect(dbname)
	cur = con.cursor()
	return con, cur


# Checks whether server's database exists
def dbCheck(id):
	if not (os.path.exists(os.path.join(os.getcwd(), f"{id}.db"))):
		print(f"[WARN] No .db found for the guild with ID: {id}.")

		con,cur = sqlConnect(f"{id}.db")
		cur.execute("CREATE TABLE 'users' ('id' INTEGER NOT NULL UNIQUE, 'username' TEXT NOT NULL, 'discriminator' INTEGER NOT NULL, 'level' INTEGER NOT NULL DEFAULT 0, 'exp' INTEGER NOT NULL DEFAULT 0, 'lastmsgtimestamp' REAL NOT NULL, PRIMARY KEY ('id'))")
		cur.execute("CREATE TABLE 'server' ('id' INTEGER NOT NULL UNIQUE, 'welcomechannelid' INTEGER, 'leavechannelid' INTEGER, PRIMARY KEY ('id'))")
		cur.execute(f"INSERT INTO server (id) VALUES ({id})")
		cur.close()
		con.commit()
		con.close()



### COMMANDS ###

# Level-checking command
@client.command(name="level")
async def level_func(ctx,member: discord.Member = commands.parameter(description="El miembro que quieres ver")):
	con, cur = sqlConnect(f"{ctx.guild.id}.db")
	cur.execute(f"SELECT level, exp FROM users WHERE id={member.id}")
	level, exp = cur.fetchone()
	cur.close()
	con.close()
	await ctx.send(f"<@{member.name}> es nivel {level} con {exp} exp")

level_func.brief = "Comprueba el nivel y experiencia de un usuario"
level_func.help = "Especifica al usuario que quieres ver nombrándolo después del comando"
	

# Change welcome channel
@client.command(name="welcomechannel")
async def welcomechannel_func(ctx,channel: discord.TextChannel = commands.parameter(description="El nuevo canal de bienvenida")):
	if not (ctx.author.guild_permissions.administrator):
		await ctx.send("Solo los admins pueden ejecutar este comando")
		return
	if not (channel.permissions_for(ctx.guild.get_member(client.user.id)).send_messages):
		await ctx.send("El bot no tiene permisos para mandar mensajes por ese canal")
		return
	if (channel.is_nsfw()):
		await ctx.send("El canal no puede ser *nsfw*")
		return
	if (channel.is_news()):
		await ctx.send("El canal no puede ser de noticias")
		return
	con, cur = sqlConnect(f"{ctx.guild.id}.db")
	cur.execute(f"UPDATE server SET welcomechannelid={channel.id} WHERE id={ctx.guild.id}")
	cur.close()
	con.commit()
	con.close()
	await ctx.send(f"El nuevo canal de bienvenida es <#{channel.id}>")

welcomechannel_func.brief = "Establece un canal de bienvenida"
welcomechannel_func.help = "Especifica el nuevo canal de bienvenida, el bot necesita permiso para mandar mensajes, y no puede ser nsfw o de news"


# Change leave channel
@client.command(name="leavechannel")
async def leave_func(ctx,channel: discord.TextChannel = commands.parameter(description="El nuevo canal de despedidas")):
	if not (ctx.author.guild_permissions.administrator):
		await ctx.send("Solo los admins pueden ejecutar este comando")
		return
	if not (channel.permissions_for(ctx.guild.get_member(client.user.id)).send_messages):
		await ctx.send("El bot no tiene permisos para mandar mensajes por ese canal")
		return
	if (channel.is_nsfw()):
		await ctx.send("El canal no puede ser *nsfw*")
		return
	if (channel.is_news()):
		await ctx.send("El canal no puede ser de noticias")
		return
	con, cur = sqlConnect(f"{ctx.guild.id}.db")
	cur.execute(f"UPDATE server SET leavechannelid={channel.id} WHERE id={ctx.guild.id}")
	cur.close()
	con.commit()
	con.close()
	await ctx.send(f"El nuevo canal de despedidas es <#{channel.id}>")

leave_func.brief = "Establece un canal de despedidas"
leave_func.help = "Especifica el nuevo canal de despedidas, el bot necesita permiso para mandar mensajes, y no puede ser nsfw o de news"


### EVENTS ###

# Event for when the bot gets online
@client.event
async def on_ready():
	print(f"[INFO] Logged in as {client.user.name}#{client.user.discriminator} - ID: {client.user.id}.")


# Event for when the bot receives a message, on guild or dm
@client.event
async def on_message(msg):
	dbCheck(msg.guild.id)
	if (msg.author == client.user):
		return
	
	checkUser(msg)
	updateLvling(msg)

	await client.process_commands(msg)


# Event for when a user joins a guild
@client.event
async def on_member_join(member: discord.Member):
	con, cur = sqlConnect(f"{member.guild.id}.db")
	cur.execute(f"SELECT welcomechannelid FROM server WHERE id={member.guild.id}")
	channelid = cur.fetchone()[0]
	cur.close()
	con.close()

	if not (channelid == None):
		await member.guild.get_channel(channelid).send(f"<@{member.id}> se ha unido al servidor!")


# Event for when a user leaves a guild
@client.event
async def on_member_remove(member: discord.Member):
	con, cur = sqlConnect(f"{member.guild.id}.db")
	cur.execute(f"SELECT leavechannelid FROM server WHERE id={member.guild.id}")
	channelid = cur.fetchone()[0]
	cur.close()
	con.close()

	if not (channelid == None):
		await member.guild.get_channel(channelid).send(f"<@{member.id}> nos ha dejado!")

# Event for when the bot is added into a guild
@client.event
async def on_guild_join(guild):
	print(f"[INFO] Bot's client joined guild {guild.name} - ID: {guild.id}.")

	# Creates the server's database if it doesn't exist yet, with it's default tables
	dbCheck(guild.id)


# Event for when the bot is removed from a guild
@client.event
async def on_guild_remove(guild):
	print(f"[INFO] Bot's client left/was removed from guild {guild.name} - ID: {guild.id}.")


# Initialize the client with the token
client.run(os.getenv("TOKEN"))
