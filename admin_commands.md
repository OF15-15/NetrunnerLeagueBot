# Admin-Commands for the Netrunner-League-Bot 

In general: for help, feature requests or any other bot problems, hit <@849206816172802068> up 


### `/create [name]`
Admin only, create a new league in this channel

### `/delete_league`
Admin only, delete the league in this channel

### `/reminder`
Admin only, pings unplayed games and shows the last round's current

### `/pair`
Admin only, pair a new round

### `/delete_round`
Admin only, delete the last round

### `/scheduled_pairing [start_time] [interval_days] [first-|second-|third_reminder_hours]`
Admin only, set up a schedule for this league. This will put up a new pairing every `interval_days` days, starting with the timestamp specified in `start_time`. You can get this timestamp for example from www.hammertime.cyou. Enter the time the first pairing should go up and take the number right to this icon: `</>`. You can also set up up to three reminders, please enter the number of hours those should remind players in the last three arguments.

### `/admin_help`
Show this command