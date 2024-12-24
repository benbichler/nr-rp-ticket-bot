import discord
from discord.ext import commands
import json
import os
import asyncio
import random
from datetime import datetime
from dotenv import load_dotenv

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


def create_html_transcript(transcript_data):
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Ticket Transcript {id}</title>
        <style>
            body {{font-family: Arial, sans-serif; margin: 20px;}}
            .message {{margin: 10px 0; padding: 10px; border-bottom: 1px solid #eee;}}
            .timestamp {{color: #666; font-size: 0.9em;}}
            .author {{font-weight: bold;}}
        </style>
    </head>
    <body>
        <h1>Ticket Transcript {id}</h1>
        <div class="info">
            <p>Opened by: {opened_by}</p>
            <p>Claimed by: {claimed_by}</p>
            <p>Closed by: {closed_by}</p>
            <p>Close reason: {reason}</p>
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
        transcript=transcript_data['transcript'].replace('\n', '<br>')
    )


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

async def save_transcript(channel):
    """Save channel transcript to a string"""
    transcript = []
    async for message in channel.history(limit=None, oldest_first=True):
        timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
        content = message.content or "None"
        for embed in message.embeds:
            content += f"\nEmbed: {embed.title} - {embed.description}"
        transcript.append(f"[{timestamp}] {message.author}: {content}")
    return "\n".join(transcript)


async def handle_ticket_close(channel, closer, reason="No reason specified"):
    ticket_id = int(channel.name.split('-')[0])
    ticket_creator = channel.guild.get_member_named(channel.name.split('-')[1].split()[0])
    staff_member = None

    if "(Claimed)" in channel.name:
        async for message in channel.history():
            if "has been claimed by" in message.content:
                staff_mention = message.content.split("claimed by ")[1]
                staff_id = int(staff_mention.strip("<@!>"))
                staff_member = channel.guild.get_member(staff_id)
                break

    transcript = await save_transcript(channel)
    category_name = channel.category.name.lower()
    ticket_type = "premium" if "premium" in category_name else "recovery" if "recovery" in category_name else "general"

    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, f"tickets/{ticket_type}/{channel.id}.json")
    html_path = os.path.join(base_dir, f"tickets/{ticket_type}/{channel.id}.html")
    
    os.makedirs(os.path.dirname(json_path), exist_ok=True)

    # Get ticket creator from the JSON file
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
            creator_id = existing_data.get('created_by_id')
            ticket_creator = channel.guild.get_member(creator_id) if creator_id else ticket_creator
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    ticket_data = {
        'ticket_id': channel.id,
        'channel_name': channel.name,
        'opened_by': ticket_creator.name if ticket_creator else "Unknown",
        'opened_by_id': ticket_creator.id if ticket_creator else None,
        'claimed_by': staff_member.name if staff_member else "Management" if ticket_type in ['premium', 'recovery', 'management'] else "Unclaimed",
        'claimed_by_id': staff_member.id if staff_member else None,
        'close_reason': reason,
        'closed_by': closer.name,
        'closed_by_id': closer.id,
        'closed_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'ticket_type': ticket_type,
        'transcript': transcript
    }
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(ticket_data, f, indent=4, ensure_ascii=False)
        
    html_content = create_html_transcript(ticket_data)
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    # Create transcript embed
    transcript_embed = discord.Embed(
        title="Ticket Closed",
        description=f"Ticket {channel.name} has been closed.",
        color=discord.Color.red()
    )
    transcript_embed.add_field(name="Ticket ID", value=ticket_id, inline=True)
    transcript_embed.add_field(name="Type", value=ticket_type.capitalize(), inline=True)
    transcript_embed.add_field(name="Opened By", value=ticket_creator.mention if ticket_creator else "Unknown", inline=True)
    transcript_embed.add_field(name="Closed By", value=closer.mention, inline=True)
    transcript_embed.add_field(name="Reason", value=reason, inline=False)
    transcript_embed.timestamp = datetime.now()

    # Send DM notifications with transcript
    for target in [ticket_creator, staff_member]:
        if target:
            try:
                dm_transcript_file = discord.File(html_path, filename=f"transcript-{ticket_id}.html")
                await target.send(embed=transcript_embed, view=TranscriptView(dm_transcript_file))
            except discord.Forbidden:
                print(f"Couldn't DM {target.name}")

    # Send to transcript channel
    transcript_channel = channel.guild.get_channel(TRANSCRIPT_CHANNEL_ID)
    if transcript_channel:
        transcript_file = discord.File(html_path, filename=f"transcript-{ticket_id}.html")
        view = TranscriptView(transcript_file)
        await transcript_channel.send(embed=transcript_embed, view=view)

    # Update staff notification channel
    staff_channel = channel.guild.get_channel(STAFF_CHANNEL_ID)
    if staff_channel:
        # Find and delete the original notification
        async for message in staff_channel.history(limit=100):
            if (message.author.bot and message.embeds and 
                len(message.embeds) > 0 and 
                message.embeds[0].title.startswith("New") and 
                str(ticket_id) in message.embeds[0].to_dict()['fields'][0]['value']):
                await message.delete()
                break
        
        # Send closure notification
        await staff_channel.send(embed=transcript_embed)

    return transcript_file

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
        await handle_ticket_close(channel, interaction.user)
        await interaction.response.send_message("Closing ticket...", ephemeral=True)
        await asyncio.sleep(5)
        await channel.delete()

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
        await handle_ticket_close(channel, interaction.user, self.reason.value)
        await interaction.response.send_message("Closing ticket...", ephemeral=True)
        await asyncio.sleep(5)
        await channel.delete()


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
    def __init__(self, transcript_file):
        super().__init__(timeout=None)
        self.transcript_file = transcript_file
    
    @discord.ui.button(label="View Transcript", style=discord.ButtonStyle.primary, custom_id="view_transcript")
    async def view_transcript(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(file=self.transcript_file, ephemeral=True)



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

        await interaction.response.send_message("You have claimed the ticket!", ephemeral=True)
        
        # Disable the claim button
        button.disabled = True
        await interaction.message.edit(view=self)

class UserTicketView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Close", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="Close Confirmation",
            description=f"Please confirm that you want to close this ticket",
            color=discord.Color.yellow()
        )
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)
        confirm_view = CloseConfirmationView(interaction.user)
        await interaction.response.send_message(embed=embed, view=confirm_view)

    @discord.ui.button(label="Close With Reason", style=discord.ButtonStyle.red, custom_id="close_with_reason")
    async def close_with_reason(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = CloseReasonModal(self.bot)
        modal.reason.label = "Reason for closing ticket"
        modal.reason.placeholder = "You must provide a reason for closing the ticket"
        await interaction.response.send_modal(modal)

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
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }

            if ticket_type in ['premium', 'recovery', 'management']:
                for role_id in MANAGEMENT_ROLE_IDS:
                    if role := guild.get_role(role_id):
                        overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

            channel = await category.create_text_channel(name=channel_name, overwrites=overwrites)

            # Ticket info embed
            info_embed = discord.Embed(
                title="NR-RP Support Ticket",
                description="Thank you for contacting NR-RP support.\nPlease be patient, and a member of our support team will be with you shortly.",
                color=discord.Color.blue()
            )

            # Add ticket type specific fields
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
            await channel.send(view=UserTicketView(self.bot))

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

                # Type specific fields
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

                if ticket_type == "general":
                    await staff_channel.send(embed=staff_notification, 
                                        view=StaffNotificationView(self.bot, channel.id))
                else:
                    await staff_channel.send(embed=staff_notification)

            await interaction.followup.send(
                f"Your ticket has been created! Check {channel.mention}", 
                ephemeral=True
            )
            # Save initial ticket data
            ticket_data = {
                'ticket_id': channel.id,
                'channel_name': channel_name,
                'created_by': interaction.user.name,
                'created_by_id': interaction.user.id,
                'ticket_type': ticket_type,
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'status': 'open'
            }

            base_dir = os.path.dirname(os.path.abspath(__file__))
            json_path = os.path.join(base_dir, f"tickets/{ticket_type}/{channel.id}.json")
            os.makedirs(os.path.dirname(json_path), exist_ok=True)
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(ticket_data, f, indent=4, ensure_ascii=False)

            return True

        except Exception as e:
            print(f"Error creating ticket: {e}")
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

    async def setup_hook(self):
        self.add_view(SupportView(self))

bot = TicketBot()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print("Role configurations loaded:")
    print(f"Management Roles: {MANAGEMENT_ROLE_IDS}")
    print(f"Admin & Tester Roles: {ADMIN_AND_TESTER_ROLE_IDS}")
    print("------")

@bot.command()
@commands.has_permissions()
async def setup(ctx):
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
    
    await ctx.send(embed=embed, view=SupportView(bot))

bot.run(DISCORD_TOKEN)