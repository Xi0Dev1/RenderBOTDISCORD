import discord
from discord.ext import commands
from datetime import datetime

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

LOG_CHANNEL_ID = 1449842538344218745

async def send_log(guild, embed):
    """Envoie un embed dans le salon de logs"""
    channel = guild.get_channel(LOG_CHANNEL_ID)
    if channel:
        try:
            await channel.send(embed=embed)
        except Exception as e:
            print(f"Erreur lors de l'envoi du log: {e}")

def create_log_embed(title, description, color):
    """Crée un embed standardisé pour les logs"""
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.now()
    )
    return embed

# ==================== LOGS MEMBRES ====================

@bot.event
async def on_member_join(member):
    """Membre rejoint le serveur"""
    embed = create_log_embed(
        "📥 Membre Rejoint",
        f"**Membre:** {member.mention} ({member})\n"
        f"**ID:** {member.id}\n"
        f"**Compte créé:** <t:{int(member.created_at.timestamp())}:R>\n"
        f"**Total membres:** {member.guild.member_count}",
        discord.Color.green()
    )
    if member.avatar:
        embed.set_thumbnail(url=member.avatar.url)
    await send_log(member.guild, embed)

@bot.event
async def on_member_remove(member):
    """Membre quitte le serveur"""
    embed = create_log_embed(
        "📤 Membre Parti",
        f"**Membre:** {member.mention} ({member})\n"
        f"**ID:** {member.id}\n"
        f"**Rôles:** {', '.join([r.mention for r in member.roles[1:]]) or 'Aucun'}\n"
        f"**Total membres:** {member.guild.member_count}",
        discord.Color.red()
    )
    if member.avatar:
        embed.set_thumbnail(url=member.avatar.url)
    await send_log(member.guild, embed)

@bot.event
async def on_member_update(before, after):
    """Membre modifié (pseudo, rôles, etc.)"""
    changes = []
    
    # Changement de pseudo
    if before.nick != after.nick:
        changes.append(f"**Pseudo:** {before.nick or 'Aucun'} ➜ {after.nick or 'Aucun'}")
    
    # Changement de rôles
    if before.roles != after.roles:
        added_roles = [r for r in after.roles if r not in before.roles]
        removed_roles = [r for r in before.roles if r not in after.roles]
        
        if added_roles:
            changes.append(f"**➕ Rôles ajoutés:** {', '.join([r.mention for r in added_roles])}")
        if removed_roles:
            changes.append(f"**➖ Rôles retirés:** {', '.join([r.mention for r in removed_roles])}")
    
    # Changement de timeout
    if before.timed_out_until != after.timed_out_until:
        if after.timed_out_until:
            changes.append(f"**🔇 Timeout jusqu'à:** <t:{int(after.timed_out_until.timestamp())}:F>")
        else:
            changes.append("**🔊 Timeout retiré**")
    
    if changes:
        embed = create_log_embed(
            "👤 Membre Modifié",
            f"**Membre:** {after.mention}\n" + "\n".join(changes),
            discord.Color.blue()
        )
        await send_log(after.guild, embed)

@bot.event
async def on_member_ban(guild, user):
    """Membre banni"""
    banner = "Inconnu"
    reason = "Aucune raison"
    
    await discord.utils.sleep_until(datetime.now())  # Petit délai pour les audit logs
    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
        if entry.target.id == user.id:
            banner = entry.user
            reason = entry.reason or "Aucune raison"
            break
    
    embed = create_log_embed(
        "🔨 Membre Banni",
        f"**Utilisateur:** {user.mention} ({user})\n"
        f"**ID:** {user.id}\n"
        f"**Banni par:** {banner}\n"
        f"**Raison:** {reason}",
        discord.Color.dark_red()
    )
    await send_log(guild, embed)

@bot.event
async def on_member_unban(guild, user):
    """Membre débanni"""
    unbanner = "Inconnu"
    
    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.unban):
        if entry.target.id == user.id:
            unbanner = entry.user
            break
    
    embed = create_log_embed(
        "✅ Membre Débanni",
        f"**Utilisateur:** {user.mention} ({user})\n"
        f"**ID:** {user.id}\n"
        f"**Débanni par:** {unbanner}",
        discord.Color.green()
    )
    await send_log(guild, embed)

# ==================== LOGS MESSAGES ====================

@bot.event
async def on_message_delete(message):
    """Message supprimé"""
    if message.author.bot:
        return
    
    deleter = "Inconnu"
    async for entry in message.guild.audit_logs(limit=1, action=discord.AuditLogAction.message_delete):
        if entry.target.id == message.author.id:
            deleter = entry.user
            break
    
    content = message.content[:1000] if message.content else "*Aucun contenu texte*"
    
    embed = create_log_embed(
        "🗑️ Message Supprimé",
        f"**Auteur:** {message.author.mention}\n"
        f"**Supprimé par:** {deleter}\n"
        f"**Salon:** {message.channel.mention}\n"
        f"**Contenu:**\n```\n{content}\n```",
        discord.Color.orange()
    )
    
    # Ajouter les pièces jointes
    if message.attachments:
        attachments = "\n".join([f"[{a.filename}]({a.url})" for a in message.attachments])
        embed.add_field(name="📎 Pièces jointes", value=attachments, inline=False)
    
    await send_log(message.guild, embed)

@bot.event
async def on_message_edit(before, after):
    """Message édité"""
    if before.author.bot or before.content == after.content:
        return
    
    before_content = before.content[:500] if before.content else "*Vide*"
    after_content = after.content[:500] if after.content else "*Vide*"
    
    embed = create_log_embed(
        "✏️ Message Édité",
        f"**Auteur:** {before.author.mention}\n"
        f"**Salon:** {before.channel.mention}\n"
        f"**[Aller au message]({after.jump_url})**",
        discord.Color.gold()
    )
    embed.add_field(name="Avant", value=f"```\n{before_content}\n```", inline=False)
    embed.add_field(name="Après", value=f"```\n{after_content}\n```", inline=False)
    
    await send_log(before.guild, embed)

@bot.event
async def on_bulk_message_delete(messages):
    """Messages supprimés en masse"""
    if not messages:
        return
    
    channel = messages[0].channel
    embed = create_log_embed(
        "🗑️ Suppression Massive",
        f"**{len(messages)} messages** supprimés dans {channel.mention}",
        discord.Color.dark_red()
    )
    await send_log(channel.guild, embed)

# ==================== LOGS SALONS ====================

@bot.event
async def on_guild_channel_create(channel):
    """Salon créé"""
    creator = "Inconnu"
    async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_create):
        if entry.target.id == channel.id:
            creator = entry.user
            break
    
    channel_type = {
        discord.ChannelType.text: "💬 Textuel",
        discord.ChannelType.voice: "🔊 Vocal",
        discord.ChannelType.category: "📁 Catégorie",
        discord.ChannelType.forum: "📋 Forum",
        discord.ChannelType.stage_voice: "🎙️ Stage"
    }.get(channel.type, "📄 Autre")
    
    embed = create_log_embed(
        "➕ Salon Créé",
        f"**Nom:** {channel.mention if hasattr(channel, 'mention') else channel.name}\n"
        f"**Type:** {channel_type}\n"
        f"**Créé par:** {creator}",
        discord.Color.green()
    )
    await send_log(channel.guild, embed)

@bot.event
async def on_guild_channel_delete(channel):
    """Salon supprimé"""
    deleter = "Inconnu"
    async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
        if entry.target.id == channel.id:
            deleter = entry.user
            break
    
    channel_type = {
        discord.ChannelType.text: "💬 Textuel",
        discord.ChannelType.voice: "🔊 Vocal",
        discord.ChannelType.category: "📁 Catégorie",
        discord.ChannelType.forum: "📋 Forum",
        discord.ChannelType.stage_voice: "🎙️ Stage"
    }.get(channel.type, "📄 Autre")
    
    embed = create_log_embed(
        "➖ Salon Supprimé",
        f"**Nom:** #{channel.name}\n"
        f"**Type:** {channel_type}\n"
        f"**Supprimé par:** {deleter}",
        discord.Color.red()
    )
    await send_log(channel.guild, embed)

@bot.event
async def on_guild_channel_update(before, after):
    """Salon modifié"""
    changes = []
    
    if before.name != after.name:
        changes.append(f"**Nom:** {before.name} ➜ {after.name}")
    
    if hasattr(before, 'topic') and before.topic != after.topic:
        changes.append(f"**Sujet:** {before.topic or 'Aucun'} ➜ {after.topic or 'Aucun'}")
    
    if before.category != after.category:
        changes.append(f"**Catégorie:** {before.category or 'Aucune'} ➜ {after.category or 'Aucune'}")
    
    if hasattr(before, 'slowmode_delay') and before.slowmode_delay != after.slowmode_delay:
        changes.append(f"**Slowmode:** {before.slowmode_delay}s ➜ {after.slowmode_delay}s")
    
    if changes:
        editor = "Inconnu"
        async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_update):
            if entry.target.id == after.id:
                editor = entry.user
                break
        
        embed = create_log_embed(
            "✏️ Salon Modifié",
            f"**Salon:** {after.mention if hasattr(after, 'mention') else after.name}\n"
            f"**Modifié par:** {editor}\n\n" + "\n".join(changes),
            discord.Color.blue()
        )
        await send_log(after.guild, embed)

# ==================== LOGS RÔLES ====================

@bot.event
async def on_guild_role_create(role):
    """Rôle créé"""
    creator = "Inconnu"
    async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_create):
        if entry.target.id == role.id:
            creator = entry.user
            break
    
    embed = create_log_embed(
        "🎭 Rôle Créé",
        f"**Nom:** {role.mention}\n"
        f"**Couleur:** {role.color}\n"
        f"**Créé par:** {creator}",
        discord.Color.green()
    )
    await send_log(role.guild, embed)

@bot.event
async def on_guild_role_delete(role):
    """Rôle supprimé"""
    deleter = "Inconnu"
    async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
        if entry.target.id == role.id:
            deleter = entry.user
            break
    
    embed = create_log_embed(
        "🎭 Rôle Supprimé",
        f"**Nom:** {role.name}\n"
        f"**Couleur:** {role.color}\n"
        f"**Supprimé par:** {deleter}",
        discord.Color.red()
    )
    await send_log(role.guild, embed)

@bot.event
async def on_guild_role_update(before, after):
    """Rôle modifié"""
    changes = []
    
    if before.name != after.name:
        changes.append(f"**📝 Nom:** {before.name} ➜ {after.name}")
    
    if before.color != after.color:
        changes.append(f"**🎨 Couleur:** {before.color} ➜ {after.color}")
    
    if before.hoist != after.hoist:
        changes.append(f"**📌 Affichage séparé:** {'✅' if after.hoist else '❌'}")
    
    if before.mentionable != after.mentionable:
        changes.append(f"**@️ Mentionnable:** {'✅' if after.mentionable else '❌'}")
    
    if before.permissions != after.permissions:
        changes.append("**🛡️ Permissions modifiées**")
    
    if before.position != after.position:
        changes.append(f"**🔢 Position:** {before.position} ➜ {after.position}")
    
    if changes:
        editor = "Inconnu"
        async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_update):
            if entry.target.id == after.id:
                editor = entry.user
                break
        
        embed = create_log_embed(
            "⚙️ Rôle Modifié",
            f"**Rôle:** {after.mention}\n"
            f"**Modifié par:** {editor}\n\n" + "\n".join(changes),
            discord.Color.blue()
        )
        await send_log(after.guild, embed)

# ==================== LOGS VOCAUX ====================

@bot.event
async def on_voice_state_update(member, before, after):
    """État vocal modifié"""
    
    # Rejoindre un salon vocal
    if before.channel is None and after.channel is not None:
        embed = create_log_embed(
            "🔊 Vocal - Connexion",
            f"**Membre:** {member.mention}\n"
            f"**Salon:** {after.channel.mention}",
            discord.Color.green()
        )
        await send_log(member.guild, embed)
    
    # Quitter un salon vocal
    elif before.channel is not None and after.channel is None:
        embed = create_log_embed(
            "🔇 Vocal - Déconnexion",
            f"**Membre:** {member.mention}\n"
            f"**Salon:** {before.channel.mention}",
            discord.Color.red()
        )
        await send_log(member.guild, embed)
    
    # Changer de salon vocal
    elif before.channel != after.channel:
        embed = create_log_embed(
            "🔁 Vocal - Déplacement",
            f"**Membre:** {member.mention}\n"
            f"**De:** {before.channel.mention}\n"
            f"**Vers:** {after.channel.mention}",
            discord.Color.blue()
        )
        await send_log(member.guild, embed)
    
    # Mute/Unmute micro
    elif before.self_mute != after.self_mute:
        status = "🎤 Micro activé" if not after.self_mute else "🔇 Micro coupé"
        embed = create_log_embed(
            "🎙️ Vocal - Micro",
            f"**Membre:** {member.mention}\n"
            f"**Salon:** {after.channel.mention}\n"
            f"**Statut:** {status}",
            discord.Color.blue()
        )
        await send_log(member.guild, embed)
    
    # Casque on/off
    elif before.self_deaf != after.self_deaf:
        status = "🔊 Casque activé" if not after.self_deaf else "🔇 Casque désactivé"
        embed = create_log_embed(
            "🎧 Vocal - Casque",
            f"**Membre:** {member.mention}\n"
            f"**Salon:** {after.channel.mention}\n"
            f"**Statut:** {status}",
            discord.Color.blue()
        )
        await send_log(member.guild, embed)
    
    # Stream
    elif before.self_stream != after.self_stream:
        status = "📺 Stream démarré" if after.self_stream else "📺 Stream arrêté"
        embed = create_log_embed(
            "📡 Vocal - Stream",
            f"**Membre:** {member.mention}\n"
            f"**Salon:** {after.channel.mention}\n"
            f"**Statut:** {status}",
            discord.Color.purple()
        )
        await send_log(member.guild, embed)
    
    # Vidéo
    elif before.self_video != after.self_video:
        status = "📹 Vidéo activée" if after.self_video else "📹 Vidéo désactivée"
        embed = create_log_embed(
            "🎥 Vocal - Vidéo",
            f"**Membre:** {member.mention}\n"
            f"**Salon:** {after.channel.mention}\n"
            f"**Statut:** {status}",
            discord.Color.purple()
        )
        await send_log(member.guild, embed)

# ==================== LOGS SERVEUR ====================

@bot.event
async def on_guild_update(before, after):
    """Serveur modifié"""
    changes = []
    
    if before.name != after.name:
        changes.append(f"**📝 Nom:** {before.name} ➜ {after.name}")
    
    if before.owner != after.owner:
        changes.append(f"**👑 Propriétaire:** {before.owner.mention} ➜ {after.owner.mention}")
    
    if before.verification_level != after.verification_level:
        changes.append(f"**🔒 Niveau de vérification:** {before.verification_level} ➜ {after.verification_level}")
    
    if changes:
        embed = create_log_embed(
            "🏠 Serveur Modifié",
            "\n".join(changes),
            discord.Color.gold()
        )
        await send_log(after, embed)

@bot.event
async def on_guild_emojis_update(guild, before, after):
    """Emojis modifiés"""
    added = [e for e in after if e not in before]
    removed = [e for e in before if e not in after]
    
    description = ""
    if added:
        description += f"**➕ Ajoutés:** {' '.join([str(e) for e in added])}\n"
    if removed:
        description += f"**➖ Retirés:** {' '.join([str(e) for e in removed])}"
    
    if description:
        embed = create_log_embed(
            "😀 Emojis Modifiés",
            description,
            discord.Color.gold()
        )
        await send_log(guild, embed)

@bot.event
async def on_invite_create(invite):
    """Invitation créée"""
    embed = create_log_embed(
        "🔗 Invitation Créée",
        f"**Code:** {invite.code}\n"
        f"**Créée par:** {invite.inviter.mention if invite.inviter else 'Inconnu'}\n"
        f"**Salon:** {invite.channel.mention}\n"
        f"**Expire:** <t:{int(invite.expires_at.timestamp())}:R>" if invite.expires_at else "Jamais",
        discord.Color.green()
    )
    await send_log(invite.guild, embed)

@bot.event
async def on_invite_delete(invite):
    """Invitation supprimée"""
    embed = create_log_embed(
        "🔗 Invitation Supprimée",
        f"**Code:** {invite.code}\n"
        f"**Salon:** {invite.channel.mention}",
        discord.Color.red()
    )
    await send_log(invite.guild, embed)

# ==================== BOT READY ====================

@bot.event
async def on_ready():
    print(f"✅ Bot connecté en tant que {bot.user}")
    print(f"📊 Serveurs: {len(bot.guilds)}")
    print(f"👥 Utilisateurs: {len(bot.users)}")
    print("=" * 50)

# BOT SUR RAILWAY COMMANDE 

import os
bot.run(os.getenv("TOKEN"))


# ==================== LANCEMENT ====================

TOKEN = "MTQ0ODcyNTc3NzU1NzM2MDc4Mg.G28E-R.EgR_QVLgsJC4Ne8YQxSYSgVBdfG3CkZoQJBfJY"
bot.run(TOKEN)