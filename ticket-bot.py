import discord
from discord.ext import commands
import json
import os
import asyncio
import random
from datetime import datetime
from dotenv import load_dotenv

import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ticket_bot.log'),
        logging.StreamHandler()
    ]
)

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
TICKET_CHANNEL_ID = int(os.getenv('TICKET_CHANNEL_ID'))
STAFF_CHANNEL_ID = int(os.getenv('STAFF_CHANNEL_ID'))
GUILD_ID = int(os.getenv('GUILD_ID'))

# Categories for different ticket types
GENERAL_CATEGORY_ID = int(os.getenv('GENERAL_CATEGORY_ID'))
PREMIUM_CATEGORY_ID = int(os.getenv('PREMIUM_CATEGORY_ID'))
RECOVERY_CATEGORY_ID = int(os.getenv('RECOVERY_CATEGORY_ID'))
MANAGEMENT_CATEGORY_ID = int(os.getenv('MANAGEMENT_CATEGORY_ID'))
TRANSCRIPT_CHANNEL_ID = int(os.getenv('TRANSCRIPT_CHANNEL_ID'))

# Parse role IDs from environment variables
def parse_role_ids(env_var):
    role_ids = os.getenv(env_var)
    if role_ids:
        return [int(id.strip()) for id in role_ids.split(',')]
    return []

MANAGEMENT_ROLE_IDS = parse_role_ids('MANAGEMENT_ROLE_IDS')
ADMIN_AND_TESTER_ROLE_IDS = parse_role_ids('ADMIN_AND_TESTER_ROLE_IDS')

# Create ticket directories if they don't exist
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TICKET_DIRS = [os.path.join(BASE_DIR, dir) for dir in ['tickets/general', 'tickets/premium', 'tickets/recovery', 'tickets/management']]
for dir in TICKET_DIRS:
    os.makedirs(dir, exist_ok=True)


'''def create_html_transcript(transcript_data):
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Ticket Transcript {id}</title>
        <style>
            :root {{
                --discord-dark: #36393f;
                --discord-darker: #2f3136;
                --discord-light: #dcddde;
                --discord-lighter: #ffffff;
                --discord-gray: #72767d;
                --discord-highlight: #5865f2;
            }}
            
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}

            body {{
                font-family: 'gg sans', 'Noto Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif;
                background-color: var(--discord-dark);
                color: var(--discord-light);
                line-height: 1.4;
                padding: 20px;
            }}

            .header {{
                background-color: var(--discord-darker);
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
            }}

            .header h1 {{
                color: var(--discord-lighter);
                font-size: 24px;
                margin-bottom: 15px;
            }}

            .info {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 10px;
                background-color: var(--discord-dark);
                padding: 15px;
                border-radius: 5px;
            }}

            .info p {{
                color: var(--discord-light);
                font-size: 14px;
            }}

            .transcript {{
                background-color: var(--discord-dark);
                border-radius: 8px;
                padding: 10px;
            }}

            .message {{
                display: flex;
                padding: 10px;
                margin: 2px 0;
                border-radius: 4px;
                transition: background-color 0.1s;
            }}

            .message:hover {{
                background-color: var(--discord-darker);
            }}

            .avatar {{
                width: 40px;
                height: 40px;
                border-radius: 50%;
                margin-right: 15px;
                background-color: var(--discord-gray);
                background-size: cover;
                background-position: center;
                flex-shrink: 0;
            }}

            .message-content {{
                flex-grow: 1;
            }}

            .message-header {{
                display: flex;
                align-items: baseline;
                margin-bottom: 4px;
            }}

            .author {{
                font-weight: 500;
                color: var(--discord-lighter);
                margin-right: 8px;
            }}

            .timestamp {{
                color: var(--discord-gray);
                font-size: 0.75rem;
            }}

            .text {{
                color: var(--discord-light);
                font-size: 1rem;
                white-space: pre-wrap;
                word-wrap: break-word;
            }}

            .embed {{
                background-color: var(--discord-darker);
                border-left: 4px solid var(--discord-highlight);
                border-radius: 4px;
                padding: 12px;
                margin: 4px 0;
            }}

            .embed-title {{
                color: var(--discord-lighter);
                font-size: 1rem;
                font-weight: 600;
                margin-bottom: 4px;
            }}

            .embed-description {{
                color: var(--discord-light);
                font-size: 0.9rem;
            }}

            .embed-field {{
                margin-top: 8px;
            }}

            .embed-field-name {{
                color: var(--discord-lighter);
                font-weight: 600;
                font-size: 0.9rem;
            }}

            .embed-field-value {{
                color: var(--discord-light);
                font-size: 0.9rem;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Ticket Transcript #{id}</h1>
            <div class="info">
                <p><strong>Opened by:</strong> {opened_by}</p>
                <p><strong>Claimed by:</strong> {claimed_by}</p>
                <p><strong>Closed by:</strong> {closed_by}</p>
                <p><strong>Close reason:</strong> {reason}</p>
            </div>
        </div>
        <div class="transcript">
            {transcript}
        </div>
    </body>
    </html>
    """.format(
        id=transcript_data['ticket_id'],
        opened_by=transcript_data['opened_by'],
        claimed_by=transcript_data['claimed_by'],
        closed_by=transcript_data['closed_by'],
        reason=transcript_data['close_reason'],
        transcript=transcript_data['transcript']
    )'''

async def create_transcript_embeds(channel, ticket_data):
    """Create a series of Discord embeds for the transcript"""
    embeds = []
    
    # Create header embed
    header_embed = discord.Embed(
        title=f"Ticket Transcript #{ticket_data['ticket_id']}",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    header_embed.add_field(name="Opened by", value=ticket_data['opened_by'], inline=True)
    header_embed.add_field(name="Claimed by", value=ticket_data['claimed_by'], inline=True)
    header_embed.add_field(name="Closed by", value=ticket_data['closed_by'], inline=True)
    header_embed.add_field(name="Close reason", value=ticket_data['close_reason'], inline=False)
    embeds.append(header_embed)
    
    # Create message embeds
    current_embed = discord.Embed(color=discord.Color.dark_theme())
    messages = []
    
    async for message in channel.history(limit=None, oldest_first=True):
        # Skip empty messages and confirmation messages
        if (not message.content and not message.embeds) or \
           (message.embeds and message.embeds[0].title == "Close Confirmation") or \
           (message.content == "Closing ticket...") or \
           (message.embeds and any(embed.title == "Close Confirmation" for embed in message.embeds)):
            continue
            
        timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
        content = message.content if message.content else ""
        
        # Format the message
        formatted_message = f"**{message.author.display_name}** · {timestamp}\n{content}\n"
        
        # If adding this message would exceed Discord's limit, create a new embed
        if len("\n".join(messages + [formatted_message])) > 4000:
            current_embed.description = "\n".join(messages)
            embeds.append(current_embed)
            current_embed = discord.Embed(color=discord.Color.dark_theme())
            messages = []
        
        messages.append(formatted_message)
        
        # Handle embeds from the original message
        for embed in message.embeds:
            if len(embeds) < 10:  # Discord has a limit of 10 embeds per message
                embeds.append(embed)
    
    # Add any remaining messages
    if messages:
        current_embed.description = "\n".join(messages)
        embeds.append(current_embed)
    
    return embeds[:10]  # Discord has a limit of 10 embeds per message


def create_ticket_info_embed(ticket_id, opened_by, closed_by=None, claimed_by="Not claimed", open_time=None, reason=None, is_closed=False):
    embed = discord.Embed(color=discord.Color.green() if not is_closed else discord.Color.red())
    embed.set_author(name="Los Santos Roleplay")
    
    embed.title = "Ticket Closed" if is_closed else "Ticket Created"

    embed.add_field(name="Ticket ID", value=str(ticket_id), inline=True)
    embed.add_field(name="Opened By", value=opened_by.mention if opened_by else "Unknown", inline=True)
    
    if closed_by:
        embed.add_field(name="Closed By", value=closed_by.mention, inline=True)

    embed.add_field(name="Open Time", value=open_time.strftime("%H:%M %Y-%m-%d") if open_time else "Unknown", inline=True)
    embed.add_field(name="Claimed By", value=claimed_by, inline=True)

    if reason:
        embed.add_field(name="Reason", value=reason, inline=False)

    if is_closed:
        embed.timestamp = datetime.now()

    return embed

'''async def save_transcript(channel):
    """Save channel transcript to a string with Discord-like HTML formatting"""
    transcript_parts = []
    async for message in channel.history(limit=None, oldest_first=True):
        # Skip messages that have no content and no embeds
        if not message.content and not message.embeds:
            continue
            
        timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
        content = message.content if message.content else ""
        
        message_html = f'<div class="message"><div class="avatar" style="background-image: url(\'{message.author.display_avatar.url}\')"></div><div class="message-content"><div class="message-header"><span class="author">{message.author.display_name}</span><span class="timestamp">{timestamp}</span></div><div class="text">{content}</div>'
        
        # Handle embeds
        for embed in message.embeds:
            embed_html = '<div class="embed">'
            if embed.title:
                embed_html += f'<div class="embed-title">{embed.title}</div>'
            if embed.description:
                embed_html += f'<div class="embed-description">{embed.description}</div>'
            
            for field in embed.fields:
                embed_html += f'<div class="embed-field"><div class="embed-field-name">{field.name}</div><div class="embed-field-value">{field.value}</div></div>'
            
            embed_html += '</div>'
            message_html += embed_html
        
        message_html += '</div></div>'
        transcript_parts.append(message_html)
    
    return '\n'.join(transcript_parts)'''


# 1. First, update the handle_ticket_close function to properly identify ticket types
async def handle_ticket_close(channel, closer, reason="No reason specified"):
    try:
        # Extract ticket number from channel name
        channel_name_parts = channel.name.split(' ')[0]
        ticket_number = channel_name_parts.split('-')[0]
        
        logging.info(f"Initiating ticket close - ID: {ticket_number}, Closer: {closer.name} ({closer.id})")
        
        # Retrieve ticket metadata
        ticket_metadata = bot.get_ticket_metadata(ticket_number)

        # Attempt to find ticket creator using stored user ID
        ticket_creator = None
        creator_name = None
        if ticket_metadata and 'user_id' in ticket_metadata:
            try:
                ticket_creator = channel.guild.get_member(ticket_metadata['user_id'])
                if ticket_creator:
                    creator_name = ticket_creator.name
            except Exception as e:
                logging.error(f"Error retrieving ticket creator by ID: {e}")
        
        # Fallback to extracting creator name from channel name if not found
        if not creator_name:
            try:
                # Split the channel name to get the creator name
                creator_name = channel.name.split('-', 1)[1]
                ticket_creator = channel.guild.get_member_named(creator_name)
                logging.info(f"Found ticket creator: {ticket_creator.name if ticket_creator else 'Not found'}")
            except Exception as e:
                logging.error(f"Error extracting creator name from channel: {e}")
                creator_name = "Unknown"
                
        stored_messages = []
        async for message in channel.history(limit=None, oldest_first=True):
            if not message.content.strip():
                continue
            stored_messages.append({
                'content': message.content,
                'author_name': message.author.name,
                'timestamp': message.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                'embeds': [embed.to_dict() for embed in message.embeds]
            })

        
        staff_member = None
        if "(Claimed)" in channel.name:
            async for message in channel.history():
                if "has been claimed by" in message.content:
                    staff_mention = message.content.split("claimed by ")[1]
                    staff_id = int(staff_mention.strip("<@!>"))
                    try:
                        staff_member = await channel.guild.fetch_member(staff_id)
                        logging.info(f"Found staff member: {staff_member.name}")
                    except Exception as e:
                        logging.error(f"Error finding staff member: {e}")
                    break

        category_name = channel.category.name.lower()
        ticket_type = (
            "premium" if "premium" in category_name
            else "recovery" if "recovery" in category_name
            else "management" if "management" in category_name
            else "general"
        )

        base_dir = os.path.dirname(os.path.abspath(__file__))
        safe_creator_name = "".join(c for c in creator_name if c.isalnum() or c in ('-', '_')).lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_base_name = f"{ticket_number}-{safe_creator_name}-{timestamp}"
        
        ticket_folder = os.path.join(base_dir, f"tickets/{ticket_type}")
        os.makedirs(ticket_folder, exist_ok=True)
        
        json_path = os.path.join(ticket_folder, f"{file_base_name}.json")

        ticket_data = {
            'ticket_id': ticket_number,
            'channel_name': channel.name, 
            'opened_by': creator_name,
            'opened_by_id': ticket_creator.id if ticket_creator else None,
            'claimed_by': staff_member.name if staff_member else "Management" if ticket_type in ['premium', 'recovery', 'management'] else "Unclaimed",
            'claimed_by_id': staff_member.id if staff_member else None,
            'close_reason': reason,
            'closed_by': closer.name,
            'closed_by_id': closer.id,
            'closed_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'ticket_type': ticket_type,
            'messages': stored_messages
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(ticket_data, f, indent=4, ensure_ascii=False)
            logging.info(f"Saved ticket data to {json_path}")

        view = TranscriptView(stored_messages, ticket_data)
        
        close_notification = discord.Embed(
            title="Ticket Closed",
            description=f"Ticket {channel.name} has been closed.",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        close_notification.add_field(name="Ticket ID", value=ticket_number, inline=True)
        close_notification.add_field(name="Type", value=ticket_type.capitalize(), inline=True)
        close_notification.add_field(name="Opened By", value=ticket_creator.mention if ticket_creator else creator_name, inline=True)
        close_notification.add_field(name="Closed By", value=closer.mention, inline=True)
        close_notification.add_field(name="Reason", value=reason, inline=False)

        # Send notifications to ticket creator and staff
        for target in [ticket_creator, staff_member]:
            if target:
                try:
                    logging.info(f"Attempting to send DM to {target.name} ({target.id})")
                    await target.send(embed=close_notification, view=view)
                    logging.info(f"Successfully sent close notification to {target.name}")
                except discord.Forbidden:
                    logging.warning(f"Couldn't DM {target.name} - DMs disabled")
                except Exception as e:
                    logging.error(f"Error DMing {target.name}: {str(e)}")

        # Send to transcript channel
        transcript_channel = channel.guild.get_channel(TRANSCRIPT_CHANNEL_ID)
        if transcript_channel:
            try:
                await transcript_channel.send(embed=close_notification, view=view)
                logging.info("Successfully sent transcript to transcript channel")
            except Exception as e:
                logging.error(f"Error sending to transcript channel: {str(e)}")

        logging.info(f"Successfully closed ticket {ticket_number}")
        return True
        
    except Exception as e:
        logging.error(f"Error in handle_ticket_close: {str(e)}")
        return False

class CloseConfirmationView(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=None)
        self.user = user

    @discord.ui.button(label="Close", style=discord.ButtonStyle.green, custom_id="confirm_close")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("You cannot use this button.", ephemeral=True)
            return
            
        channel = interaction.channel
        try:
            # Save transcript first
            await handle_ticket_close(channel, interaction.user, "Closed without reason")
            await interaction.response.send_message("Closing ticket...", ephemeral=True)
            await asyncio.sleep(5)
            await channel.delete()
        except Exception as e:
            await interaction.response.send_message(f"Error closing ticket: {str(e)}", ephemeral=True)

class CloseReasonModal(discord.ui.Modal, title="Close Ticket"):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.reason = discord.ui.TextInput(
            label="Reason",
            placeholder="Enter the reason for closing...",
            required=True,
            max_length=1000
        )
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        channel = interaction.channel
        try:
            # Save transcript with the provided reason
            await handle_ticket_close(channel, interaction.user, self.reason.value)
            await interaction.response.send_message("Closing ticket...", ephemeral=True)
            await asyncio.sleep(5)
            await channel.delete()
        except Exception as e:
            await interaction.response.send_message(f"Error closing ticket: {str(e)}", ephemeral=True)


class ManagementSupportModal(discord.ui.Modal, title="Management Support"):
    def __init__(self):
        super().__init__()
        self.issue = discord.ui.TextInput(
            label="PLEASE DESCRIBE THE ISSUE YOU ARE FACING",
            style=discord.TextStyle.paragraph,
            placeholder="Please note this channel is for important management issues only.",
            required=True,
            max_length=1024
        )
        self.acknowledgment = discord.ui.TextInput(
            label="Type 'I ACKNOWLEDGE' to confirm",
            placeholder="This ticket system should only be used for important management issues",
            required=True,
            max_length=13
        )
        self.add_item(self.issue)
        self.add_item(self.acknowledgment)

    async def on_submit(self, interaction: discord.Interaction):
        if self.acknowledgment.value.upper() != "I ACKNOWLEDGE":
            await interaction.response.send_message("You must acknowledge the terms by typing 'I ACKNOWLEDGE'", ephemeral=True)
            return
            
        await interaction.response.defer()
        view = SupportView(interaction.client)
        await view.create_ticket(interaction, "management", self)


class GeneralSupportModal(discord.ui.Modal, title="General Support"):
    def __init__(self):
        super().__init__()
        self.issue = discord.ui.TextInput(
            label="PLEASE DESCRIBE THE ISSUE YOU ARE FACING",
            style=discord.TextStyle.paragraph,
            placeholder="Describe your issue...",
            required=True,
            max_length=1024
        )
        self.add_item(self.issue)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        view = SupportView(interaction.client)
        await view.create_ticket(interaction, "general", self)

class AccountRecoveryModal(discord.ui.Modal, title="Account Support"):
    def __init__(self):
        super().__init__()
        self.character_name = discord.ui.TextInput(
            label="CHARACTER NAME",
            required=True,
            max_length=100,
            placeholder="Use Firstname_Lastname format"
        )
        self.issue = discord.ui.TextInput(
            label="PLEASE DESCRIBE THE ISSUE YOU ARE FACING",
            style=discord.TextStyle.paragraph,
            placeholder="Describe your issue...",
            required=True,
            max_length=1024
        )
        self.add_item(self.character_name)
        self.add_item(self.issue)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        view = SupportView(interaction.client)
        await view.create_ticket(interaction, "recovery", self)

class BillingSupportModal(discord.ui.Modal, title="Billing Support"):
    def __init__(self):
        super().__init__()
        self.character_name = discord.ui.TextInput(
            label="CHARACTER NAME",
            required=True,
            max_length=100,
            placeholder="Use Firstname_Lastname format"
        )
        self.email = discord.ui.TextInput(
            label="EMAIL ADDRESS",
            required=True,
            max_length=100
        )
        self.issue = discord.ui.TextInput(
            label="PLEASE DESCRIBE THE ISSUE YOU ARE FACING",
            style=discord.TextStyle.paragraph,
            placeholder="Describe your issue...",
            required=True,
            max_length=1024
        )
        self.add_item(self.character_name)
        self.add_item(self.email)
        self.add_item(self.issue)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        view = SupportView(interaction.client)
        await view.create_ticket(interaction, "premium", self)

class TranscriptView(discord.ui.View):
    def __init__(self, messages, ticket_data):
        super().__init__(timeout=None)
        self.messages = messages
        self.ticket_data = ticket_data
    
    @discord.ui.button(label="View Transcript", style=discord.ButtonStyle.primary, emoji="📄")
    async def view_transcript(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            logging.info(f"User {interaction.user.name} viewing transcript for ticket {self.ticket_data['ticket_id']}")
            await interaction.response.defer(ephemeral=True)
            
            embeds = []
            header_embed = discord.Embed(
                title=f"Ticket Transcript #{self.ticket_data['ticket_id']}",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            header_embed.add_field(name="Opened by", value=self.ticket_data['opened_by'], inline=True)
            header_embed.add_field(name="Claimed by", value=self.ticket_data['claimed_by'], inline=True)
            header_embed.add_field(name="Closed by", value=self.ticket_data['closed_by'], inline=True)
            header_embed.add_field(name="Close reason", value=self.ticket_data['close_reason'], inline=False)
            embeds.append(header_embed)

            current_embed = discord.Embed(color=discord.Color.dark_theme())
            current_messages = []
            
            for msg in self.messages:
                if not msg['content'].strip():
                    continue
                    
                formatted_message = f"**{msg['author_name']}** · {msg['timestamp']}\n{msg['content']}\n"
                
                if len("\n".join(current_messages + [formatted_message])) > 4000:
                    current_embed.description = "\n".join(current_messages)
                    embeds.append(current_embed)
                    current_embed = discord.Embed(color=discord.Color.dark_theme())
                    current_messages = []
                
                current_messages.append(formatted_message)
            
            if current_messages:
                current_embed.description = "\n".join(current_messages)
                embeds.append(current_embed)
            
            await interaction.followup.send(embeds=embeds[:10], ephemeral=True)
            logging.info(f"Successfully displayed transcript for ticket {self.ticket_data['ticket_id']}")
        except Exception as e:
            logging.error(f"Error displaying transcript: {str(e)}")
            await interaction.followup.send("An error occurred while displaying the transcript.", ephemeral=True)



class StaffNotificationView(discord.ui.View):
    def __init__(self, bot, ticket_channel_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.ticket_channel_id = ticket_channel_id

    @discord.ui.button(label="Claim Ticket", style=discord.ButtonStyle.green, custom_id="claim_notification")
    async def claim_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check if user has staff role
        if not any(role.id in ADMIN_AND_TESTER_ROLE_IDS for role in interaction.user.roles):
            await interaction.response.send_message("You don't have permission to claim tickets!", ephemeral=True)
            return

        ticket_channel = interaction.guild.get_channel(self.ticket_channel_id)
        if not ticket_channel:
            await interaction.response.send_message("Ticket channel not found!", ephemeral=True)
            return

        if "(Claimed)" in ticket_channel.name:
            await interaction.response.send_message("This ticket is already claimed!", ephemeral=True)
            return

        # Add staff member to the channel
        await ticket_channel.set_permissions(interaction.user, read_messages=True, send_messages=True)
        await ticket_channel.edit(name=f"{ticket_channel.name} (Claimed)")

        # Create and send embed message
        claim_embed = discord.Embed(
            description=f"👋 {interaction.user.mention} has claimed your ticket and will assist you shortly.",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        system_message = await ticket_channel.send(embed=claim_embed)
        await system_message.pin()

        await interaction.response.send_message("You have claimed the ticket!", ephemeral=True)
        
        # Disable the claim button
        button.disabled = True
       
        await interaction.message.edit(view=self)

class UserSelectMenu(discord.ui.Select):
    def __init__(self, users):
        options = [
            discord.SelectOption(
                label=user.name[:25],
                description=f"ID: {user.id}"[:50] if user.id else "No ID",
                value=str(user.id)
            ) for user in users[:25]
        ]
        super().__init__(
            placeholder="Select users to add...",
            min_values=1,
            max_values=min(len(options), 25),
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        # Get selected members
        selected_members = []
        for value in self.values:
            member = interaction.guild.get_member(int(value))
            if member:
                selected_members.append(member)

        if not selected_members:
            await interaction.followup.send("No valid users were selected.", ephemeral=True)
            return

        # Add users immediately
        added_users = []
        failed_users = []

        for member in selected_members:
            try:
                await interaction.channel.set_permissions(member,
                    read_messages=True,
                    send_messages=True,
                    attach_files=True,
                    embed_links=True
                )
                added_users.append(member)
            except Exception as e:
                failed_users.append((member, str(e)))

        # Send results
        if added_users:
            # Send a notification in the ticket channel
            notification = discord.Embed(
                description=f"✅ {interaction.user.mention} added {', '.join([member.mention for member in added_users])} to the ticket",
                color=discord.Color.green()
            )
            await interaction.channel.send(embed=notification)

            #  Add this DM notification code here
            dm_embed = discord.Embed(
                title="Added to Support Ticket",
                description=f"You have been added to a support ticket in {interaction.guild.name}",
                color=discord.Color.blue()
            )
            dm_embed.add_field(name="Channel", value=f"#{interaction.channel.name}", inline=False)
            dm_embed.add_field(name="Added By", value=interaction.user.name, inline=False)
            dm_embed.add_field(name="Click to View", value=interaction.channel.jump_url, inline=False)
            
            for member in added_users:
                try:
                    await member.send(embed=dm_embed)
                except discord.Forbidden:
                    logging.info(f"Could not DM user {member.name}")

            # Send ephemeral confirmation to staff member
            await interaction.followup.send(
                f"Successfully added {len(added_users)} user(s) to the ticket.", 
                ephemeral=True
            )

        if failed_users:
            failures = "\n".join([f"• {member.name}" for member, _ in failed_users])
            await interaction.followup.send(
                f"Failed to add the following users:\n{failures}", 
                ephemeral=True
            )

class AddUserConfirmationView(discord.ui.View):
    def __init__(self, members):
        super().__init__(timeout=300)  # 5 minute timeout
        self.members = members

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        added_users = []
        failed_users = []

        for member in self.members:
            try:
                await interaction.channel.set_permissions(member,
                    read_messages=True,
                    send_messages=True
                )
                added_users.append(member)
            except Exception as e:
                failed_users.append((member, str(e)))

        # Create result embed
        embed = discord.Embed(
            title="Users Added to Ticket",
            color=discord.Color.green() if added_users else discord.Color.red(),
            timestamp=datetime.now()
        )

        if added_users:
            users_added = "\n".join([f"• {member.mention}" for member in added_users])
            embed.add_field(
                name=f"Successfully Added ({len(added_users)} users)",
                value=users_added,
                inline=False
            )

        if failed_users:
            failures = "\n".join([f"• {member.name} - {error}" for member, error in failed_users])
            embed.add_field(
                name=f"Failed to Add ({len(failed_users)} users)",
                value=failures,
                inline=False
            )

        # Send ephemeral response with results
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # Delete the original confirmation message
        await interaction.message.delete()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Delete the original confirmation message
        await interaction.message.delete()
        
        # Send ephemeral cancellation message
        embed = discord.Embed(
            description="❌ User addition cancelled",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    def disable_all_buttons(self):
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

class AddUserView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Add Users", style=discord.ButtonStyle.primary, custom_id="search_user", emoji="👥")
    async def search_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(role.id in ADMIN_AND_TESTER_ROLE_IDS for role in interaction.user.roles):
            await interaction.response.send_message("You don't have permission to add users!", ephemeral=True)
            return

        await interaction.response.send_modal(UserSearchModal())

class UserSearchModal(discord.ui.Modal, title="Search Server Member"):
    def __init__(self):
        super().__init__()
        self.search = discord.ui.TextInput(
            label="Search by username",
            placeholder="Enter part of the username...",
            required=True,
            max_length=100
        )
        self.add_item(self.search)

    async def on_submit(self, interaction: discord.Interaction):
        search_term = self.search.value.lower()
        
        matching_members = [
            member for member in interaction.guild.members
            if search_term in member.name.lower() or 
               search_term in (member.nick.lower() if member.nick else "")
        ]

        if not matching_members:
            await interaction.response.send_message("No users found matching that search.", ephemeral=True)
            return

        select_menu = UserSelectMenu(matching_members)
        view = discord.ui.View(timeout=60)
        view.add_item(select_menu)
        
        # Send ephemeral selection menu
        await interaction.response.send_message(
            "Select users to add to the ticket:",
            view=view,
            ephemeral=True
        )

class UserTicketView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    def is_staff(self, user):
        if isinstance(user, discord.Member):
            return any(role.id in (ADMIN_AND_TESTER_ROLE_IDS + MANAGEMENT_ROLE_IDS) for role in user.roles)
        return False

    def get_ticket_creator_id(self, channel):
        # Assuming ticket creator ID is stored in channel topic
        if channel.topic and channel.topic.isdigit():
            return int(channel.topic)
        return None

    @discord.ui.button(label="Close", style=discord.ButtonStyle.red, custom_id="close_ticket", row=0)
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="Close Confirmation",
            description=f"Please confirm that you want to close this ticket",
            color=discord.Color.yellow()
        )
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)
        confirm_view = CloseConfirmationView(interaction.user)
        await interaction.response.send_message(embed=embed, view=confirm_view)

    @discord.ui.button(label="Close With Reason", style=discord.ButtonStyle.red, custom_id="close_with_reason", row=0)
    async def close_with_reason(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = CloseReasonModal(self.bot)
        modal.reason.label = "Reason for closing ticket"
        modal.reason.placeholder = "You must provide a reason for closing the ticket"
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Add Users", style=discord.ButtonStyle.green, custom_id="add_user", emoji="👥", row=1)
    async def add_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check if user is staff
        if not self.is_staff(interaction.user):
            await interaction.response.send_message("You don't have permission to add users!", ephemeral=True)
            return
        
        # Check if user is the ticket creator
        ticket_creator_id = self.get_ticket_creator_id(interaction.channel)
        if interaction.user.id == ticket_creator_id:
            await interaction.response.send_message("As the ticket creator, you cannot add users!", ephemeral=True)
            return
            
        await interaction.response.send_modal(UserSearchModal())

    @discord.ui.button(label="Remove Users", style=discord.ButtonStyle.secondary, custom_id="remove_user", emoji="🚫", row=1)
    async def remove_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check if user is staff
        if not self.is_staff(interaction.user):
            await interaction.response.send_message("You don't have permission to remove users!", ephemeral=True)
            return
        
        # Check if user is the ticket creator
        ticket_creator_id = self.get_ticket_creator_id(interaction.channel)
        if interaction.user.id == ticket_creator_id:
            await interaction.response.send_message("As the ticket creator, you cannot remove users!", ephemeral=True)
            return

        # Get all users with explicit permissions in the channel
        removable_users = []
        for overwrite in interaction.channel.overwrites:
            if isinstance(overwrite, discord.Member) and overwrite.id != interaction.guild.me.id:
                removable_users.append(overwrite)

        if not removable_users:
            await interaction.response.send_message("No users can be removed from this ticket.", ephemeral=True)
            return

        # Create select menu with removable users
        select_menu = RemoveUserSelectMenu(removable_users)
        view = discord.ui.View(timeout=60)
        view.add_item(select_menu)
        
        await interaction.response.send_message(
            "Select users to remove from the ticket:",
            view=view,
            ephemeral=True
        )
        
    
class RemoveUserSelectMenu(discord.ui.Select):
    def __init__(self, users):
        options = [
            discord.SelectOption(
                label=user.name[:25],
                description=f"ID: {user.id}"[:50] if user.id else "No ID",
                value=str(user.id)
            ) for user in users[:25]
        ]
        super().__init__(
            placeholder="Select users to remove...",
            min_values=1,
            max_values=min(len(options), 25),
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        selected_members = []
        for value in self.values:
            member = interaction.guild.get_member(int(value))
            if member:
                selected_members.append(member)

        if not selected_members:
            await interaction.followup.send("No valid users were selected.", ephemeral=True)
            return

        # Remove users immediately
        removed_users = []
        failed_users = []

        for member in selected_members:
            try:
                await interaction.channel.set_permissions(member, overwrite=None)  # Remove permissions
                removed_users.append(member)
            except Exception as e:
                failed_users.append((member, str(e)))

        # Send results
        if removed_users:
            # Send a notification in the ticket channel
            notification = discord.Embed(
                description=f"❌ {interaction.user.mention} removed {', '.join([member.mention for member in removed_users])} from the ticket",
                color=discord.Color.red()
            )
            await interaction.channel.send(embed=notification)

            # Add this DM notification code here
            dm_embed = discord.Embed(
                title="Removed from Support Ticket",
                description=f"You have been removed from a support ticket in {interaction.guild.name}",
                color=discord.Color.red()
            )
            dm_embed.add_field(name="Channel", value=f"#{interaction.channel.name}", inline=False)
            dm_embed.add_field(name="Removed By", value=interaction.user.name, inline=False)
            
            for member in removed_users:
                try:
                    await member.send(embed=dm_embed)
                except discord.Forbidden:
                    logging.info(f"Could not DM user {member.name}")

            # Send ephemeral confirmation to staff member
            await interaction.followup.send(
                f"Successfully removed {len(removed_users)} user(s) from the ticket.", 
                ephemeral=True
            )

        if failed_users:
            failures = "\n".join([f"• {member.name}" for member, _ in failed_users])
            await interaction.followup.send(
                f"Failed to remove the following users:\n{failures}", 
                ephemeral=True
            )

class SupportView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="General Support", style=discord.ButtonStyle.grey, custom_id="general_support", emoji="🎮")
    async def general_support(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = GeneralSupportModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Premium Support", style=discord.ButtonStyle.grey, custom_id="premium_support", emoji="💎")
    async def premium_support(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = BillingSupportModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Account Recovery", style=discord.ButtonStyle.grey, custom_id="account_recovery", emoji="🔑")
    async def account_recovery(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = AccountRecoveryModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Management Support", style=discord.ButtonStyle.grey, custom_id="management_support", emoji="✉️")
    async def management_support(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal=ManagementSupportModal()
        await interaction.response.send_modal(modal)   

    async def create_ticket(self, interaction: discord.Interaction, ticket_type: str, modal):
        try:
            guild = interaction.guild
            ticket_number = random.randint(1000, 9999)
            channel_name = f"{ticket_number}-{interaction.user.name}"
            
            category = guild.get_channel(self.bot.ticket_configs[ticket_type]['category_id'])

            # Define Ben's user ID
          #  BEN_USER_ID = 220880488875687936
          #  ben_user = guild.get_member(BEN_USER_ID)

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(
                    read_messages=True, 
                    send_messages=True,
                    attach_files=True,  # Allow uploading files
                    embed_links=True    # Allow embedding links
                ),
                guild.me: discord.PermissionOverwrite(
                    read_messages=True, 
                    send_messages=True,
                    attach_files=True,
                    embed_links=True
                )
            }
            # Add Ben's permissions if he's in the server and has sufficient permissions
           # if ben_user and (
           #     ben_user.guild_permissions.administrator or 
            #    any(role.id in ADMIN_AND_TESTER_ROLE_IDS for role in ben_user.roles) or
            #    any(role.id in MANAGEMENT_ROLE_IDS for role in ben_user.roles)
          #  ):
           #     overwrites[ben_user] = discord.PermissionOverwrite(
            #        read_messages=True,
             #       send_messages=True,
             #       attach_files=True,
             #       embed_links=True,
             #       manage_messages=True,
             #       manage_channels=True
              #  )

            if ticket_type in ['premium', 'recovery', 'management']:
                for role_id in MANAGEMENT_ROLE_IDS:
                    if role := guild.get_role(role_id):
                        overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

            channel = await category.create_text_channel(name=channel_name, overwrites=overwrites)
            self.bot.save_ticket_metadata(ticket_number, interaction.user.id, channel.id)

            # Ticket info embed
            info_embed = discord.Embed(
                title="NR-RP Support Ticket",
                description="Thank you for contacting NR-RP support.\nPlease be patient, and a member of our support team will be with you shortly.",
                color=discord.Color.blue()
            )

            # Add ticket type specific fields (keep your existing fields)
            if ticket_type == "general":
                info_embed.add_field(name="Issue Description", value=modal.issue.value)
            elif ticket_type=="recovery":
                info_embed.add_field(name="Character Name", value=modal.character_name.value)
                info_embed.add_field(name="Issue Description", value=modal.issue.value)
            elif ticket_type=="premium":
                info_embed.add_field(name="Character Name", value=modal.character_name.value)
                info_embed.add_field(name="Email", value=modal.email.value)
                info_embed.add_field(name="Issue Description", value=modal.issue.value)
            elif ticket_type=="management":
                info_embed.add_field(name="Issue Description", value=modal.issue.value)
                info_embed.add_field(name="Management Notice", value="This ticket was created with proper acknowledgment", inline=False)

            await channel.send(embed=info_embed)

            # Create and send the ticket view with appropriate buttons
            view = UserTicketView(self.bot)
            await channel.send(view=view)

            # Staff notification with type-specific styling
            if staff_channel := guild.get_channel(STAFF_CHANNEL_ID):
                notification_color = {
                    'general': discord.Color.green(),
                    'premium': discord.Color.gold(),
                    'recovery': discord.Color.red(),
                    'management': discord.Color.purple()
                }[ticket_type]

                staff_notification = discord.Embed(
                    title=f"New {ticket_type.capitalize()} Support Ticket",
                    color=notification_color,
                    timestamp=datetime.now()
                )

                # Base fields
                staff_notification.add_field(name="Ticket ID", value=ticket_number, inline=True)
                staff_notification.add_field(name="Created By", value=interaction.user.mention, inline=True)
                staff_notification.add_field(name="Channel", value=channel.mention, inline=True)

                # Type specific fields (keep your existing fields)
                if ticket_type=="premium":
                    staff_notification.add_field(name="Character Name", value=modal.character_name.value, inline=True)
                    staff_notification.add_field(name="Email", value=modal.email.value, inline=True)
                    staff_notification.description = f"Issue: {modal.issue.value}"
                elif ticket_type=="recovery":
                    staff_notification.add_field(name="Character Name", value=modal.character_name.value, inline=True)
                    staff_notification.description = f"Issue: {modal.issue.value}"
                elif ticket_type=="management":
                    staff_notification.add_field(name="Issue Description", value=modal.issue.value)
                    staff_notification.add_field(name="Acknowledgment", value="User has acknowledged proper usage", inline=True)
                else:
                    staff_notification.description = f"Issue: {modal.issue.value}"

                # Add role mention based on ticket type
                role_mention = ""
                if ticket_type == "general":
                    # Mention admins and testers for general tickets
                    role_mentions = [f"<@&{role_id}>" for role_id in ADMIN_AND_TESTER_ROLE_IDS]
                    role_mention = " ".join(role_mentions)
                elif ticket_type in ["premium", "recovery", "management"]:
                    # Mention management roles for premium, recovery, and management tickets
                    role_mentions = [f"<@&{role_id}>" for role_id in MANAGEMENT_ROLE_IDS]
                    role_mention = " ".join(role_mentions)

                # Send notification with role mentions
                if ticket_type == "general":
                    await staff_channel.send(content=role_mention, embed=staff_notification, 
                                        view=StaffNotificationView(self.bot, channel.id))
                else:
                    await staff_channel.send(content=role_mention, embed=staff_notification)

            await interaction.followup.send(
                f"Your ticket has been created! Check {channel.mention}", 
                ephemeral=True
            )

            return True

        except Exception as e:
                logging.error(f"Error creating ticket: {e}")
                await interaction.followup.send("An error occurred while creating the ticket.", ephemeral=True)
                return False
    
class TicketBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='!',
            intents=discord.Intents.all(),
            activity=discord.Activity(type=discord.ActivityType.playing, name="New Rotterdam Roleplay")
        )
        
        self.ticket_configs = {
            'general': {
                'staff_roles': ADMIN_AND_TESTER_ROLE_IDS,
                'category_id': GENERAL_CATEGORY_ID,
                'folder': 'tickets/general',
            },
            'premium': {
                'staff_roles': MANAGEMENT_ROLE_IDS,
                'category_id': PREMIUM_CATEGORY_ID,
                'folder': 'tickets/premium',
            },
            'recovery': {
                'staff_roles': MANAGEMENT_ROLE_IDS,
                'category_id': RECOVERY_CATEGORY_ID,
                'folder': 'tickets/recovery',
            },
            'management':{
                'staff_roles': MANAGEMENT_ROLE_IDS,
                'category_id': MANAGEMENT_CATEGORY_ID,
                'folder': 'tickets/management',
            }
        }

        # New attribute to track ticket metadata
        self.ticket_metadata = {}

    def save_ticket_metadata(self, ticket_number, user_id, channel_id):
        """Save metadata for a newly created ticket"""
        self.ticket_metadata[str(ticket_number)] = {
            'user_id': user_id,
            'channel_id': channel_id
        }
        
        # Optional: Limit metadata size to prevent memory growth
        if len(self.ticket_metadata) > 1000:
            # Remove oldest tickets if exceeding 1000
            oldest_tickets = sorted(self.ticket_metadata.keys())[:100]
            for ticket in oldest_tickets:
                del self.ticket_metadata[ticket]

    def get_ticket_metadata(self, ticket_number):
        """Retrieve metadata for a specific ticket"""
        return self.ticket_metadata.get(str(ticket_number))

    async def setup_hook(self):
        self.add_view(SupportView(self))

    async def setup_support_message(self):
        channel = self.get_channel(TICKET_CHANNEL_ID)
        if channel:
            # Clear existing messages in the channel
            await channel.purge()
            
            embed = discord.Embed(
                title="NR-RP Support System",
                description="Welcome to our support system. Select the appropriate category below:",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="🎮 General Support",
                value="For general questions, bug reports, and in-game issues.",
                inline=False
            )
            
            embed.add_field(
                name="💎 Billing Support",
                value="For donation-related inquiries and premium feature support.",
                inline=False
            )
            
            embed.add_field(
                name="🔑 Account Recovery",
                value="For account-related issues and recovery requests.",
                inline=False
            )
            
            embed.add_field(
                name="✉️ Management Support",
                value="For management-only communications. Restricted access.",
                inline=False
            )
            
            embed.set_footer(text="Please select the most appropriate category for faster assistance.")
            
            await channel.send(embed=embed, view=SupportView(self))

bot = TicketBot()


@bot.event
async def on_ready():
    logging.info(f'Connected to bot: {bot.user.name}')
    logging.info(f'Bot ID: {bot.user.id}')
    logging.info(f"Discord Version: {discord.__version__}")
    logging.info("Role configurations loaded:")
    logging.info(f"Management Roles: {MANAGEMENT_ROLE_IDS}")
    logging.info(f"Admin & Tester Roles: {ADMIN_AND_TESTER_ROLE_IDS}")
    logging.info(f"Guild ID: {GUILD_ID}")
    logging.info(f"Ticket Channel ID: {TICKET_CHANNEL_ID}")
    logging.info(f"Staff Channel ID: {STAFF_CHANNEL_ID}")
    logging.info(f"Transcript Channel ID: {TRANSCRIPT_CHANNEL_ID}")
    logging.info("Category IDs:")
    logging.info(f"- General: {GENERAL_CATEGORY_ID}")
    logging.info(f"- Premium: {PREMIUM_CATEGORY_ID}")
    logging.info(f"- Recovery: {RECOVERY_CATEGORY_ID}")
    logging.info(f"- Management: {MANAGEMENT_CATEGORY_ID}")
    logging.info("------")
    
    try:
        guild = bot.get_guild(GUILD_ID)
        if not guild:
            logging.error(f"ERROR: Could not find guild with ID {GUILD_ID}")
            return

        ticket_channel = guild.get_channel(TICKET_CHANNEL_ID)
        if not ticket_channel:
            logging.error(f"ERROR: Could not find ticket channel with ID {TICKET_CHANNEL_ID}")
            return

        staff_channel = guild.get_channel(STAFF_CHANNEL_ID)
        if not staff_channel:
            logging.error(f"ERROR: Could not find staff channel with ID {STAFF_CHANNEL_ID}")
            return

        # Set up the initial support message
        await bot.setup_support_message()
        logging.info("Successfully set up support message!")
        
    except Exception as e:
        logging.error(f"Error during initialization: {str(e)}")
        

bot.run(DISCORD_TOKEN)