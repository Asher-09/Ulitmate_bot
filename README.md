
# OT's BOT

This bot is made for OT . It is a multipropose bot with moderation , roles customization and server customization . 




## Authors

- [@Asher-09](https://www.github.com/Asher-09)



![Logo](https://imgs.search.brave.com/qWkdY3bHpnBLpakAVN3TiKqPE_WTtePcKuqtVuDMVRw/rs:fit:860:0:0:0/g:ce/aHR0cHM6Ly93d3cu/d2Vid2lzZS5pZS93/cC1jb250ZW50L3Vw/bG9hZHMvMjAxOS8x/MS9JTUcwMDEuanBn)


## Features

# - Help System -

 **help** - Opens an interactive dropdown help menu with all command categories and server info.

   | Syntax: !help |

 **help <command>** - Shows syntax and example for a specific command.

   | Syntax: !help snipe |

# - Moderation - (Mod+) [Mod, Admin, Owner, Bot Owner]

 **snipe (sn, s)** - Show last deleted message in the channel.

   | Syntax: !snipe or !snipe #general |

 **editsnipe (es)** - Show last edited message.

   | Syntax: !editsnipe |

 **warn (w)** - Warn a user.

   | Syntax: !warn @user reason |

 **warnings (ws)** - View warnings of a user.

   | Syntax: !warnings @user |

 **mute (m)** - Mute a user for a duration (e.g., 10m, 1h, 2d).

   | Syntax: !mute @user 30m spamming |

 **unmute (um)** - Manually unmute a user.

 
   | Syntax: !unmute @user |
 
 **nickname (nick)** - Change or reset a member's nickname.
 
   | Syntax: !nick @user NewName or !nick @user (to reset) |
 
 **clearwarns (cw)** - Clear all warnings of a user (Mod+? Admin? actual: 
 admin+).
 
   | Syntax: !clearwarns @user |

# - Moderation (Admin+) [Admin+ only]

 **purge (clear, clean, prune)** - Delete messages up to 500. Optional mode: bots, embeds, mentions, attachments, text, user.

   | Syntax: !purge 20, !purge bots 10, !purge user 15 @user |

 **slowmode (sm)** - Set channel slowmode (0 = off).

   | Syntax: !slowmode 5 |

 **lock** - Prevent @everyone from sending messages in a channel.

   | Syntax: !lock #general |

 **unlock** - Allow @everyone to send messages again.

   | Syntax: !unlock #general |

 **kick (k)** - Kick a member from the server.

   | Syntax: !kick @user reason |

 **ban (b)** - Ban a member from the server.

   | Syntax: !ban @user reason |

 **jail (j)** - Jail a user (creates a private cell channel).

   | Syntax: !jail @user reason |

 **unjail (uj)** - Unjail a user and delete the cell.

   | Syntax: !unjail @user |

 **say (echo)** - Make the bot speak in a channel.

   | Syntax: !say #general Hello |

 **addmod (am)** - Promote a user to staff level "Mod".

   | Syntax: !addmod @user |

 **removemod (rm)** - Demote from Mod.

   | Syntax: !removemod @user |


# - Moderation (Owner+) [Owner+ only]


 **addadmin (aa)** - Promote a user to staff level "Admin".

   | Syntax: !addadmin @user |

 **removeadmin (ra)** - Demote from Admin.

   | Syntax: !removeadmin @user |



# - Moderation (Bot Owner) [Bot Owner only]

 **addowner (ao)** - Promote a user to staff level "Owner".

   | Syntax: !addowner @user |

 **removeowner (ro)** - Demote from Owner.

   | Syntax: !removeowner @user |


# - Roles (Public) -


 **roleinfo (ri)** - Show details about a role (color, position, members).

   | Syntax: !roleinfo @Moderator |

 **rolelist (roles, listroles)** - List all server roles ranked by position 
 (1 = highest).
 
   | Syntax: !roles |



# - Roles (Admin+) -



 **createrole (cr)** - Create a new role.

   | Syntax: !createrole VIP |

 **deleterole (dr)** - Delete a role.

   | Syntax: !deleterole @VIP |

 **giverole (gr)** - Assign a role to a member.

   | Syntax: !giverole @user @VIP |

 **removerole (rr)** - Remove a role from a member.

   | Syntax: !removerole @user @VIP |

 **renamerole (rnrole)** - Rename a role.

   | Syntax: !renamerole @VIP Important |

 **colorrole (rolecolor, crcolor)** - Change a role's color (hex, e.g., 
 #FF0000).
 
   | Syntax: !colorrole @VIP #FF0000 |
 
 **roleposition (rpos, move)** - Move a role to a specific position (1 = top).
 
   | Syntax: !roleposition @Mod 3 |
 
 **rolehoist (hoist)** - Toggle role's separate display in member list.
 
   | Syntax: !rolehoist @VIP true |
 
 **rolementionable (mentionable)** - Toggle if the role can be @mentioned.
 
   | Syntax: !rolementionable @VIP true |


# - Server Utilities (Public) -



 **serverinfo (si)** - Show server name, owner, members, channels, creation date.

   | Syntax: !serverinfo |

 **userinfo (ui)** - Show member info (join date, roles, account creation).

   | Syntax: !userinfo @user or !ui |

 **avatar (av)** - Display a user's full-size avatar.

   | Syntax: !avatar @user |

 **banner** - Display a user's banner (if any).

   | Syntax: !banner @user |


## Tech Stack

**Languages :** Python

**API :** Discord.py , OS , JSON
