# Commands for Netrunner-League-Bot

| command                                                                     | description                                                   | admin only |
|-----------------------------------------------------------------------------|---------------------------------------------------------------|------------|
| `/create [name]`                                                            | create a new league                                           | x          |
| `/join`                                                                     | Join the league in this channel                               |            |
| `/leave`                                                                    | Leave the league in this channel                              |            |
| `/status`                                                                   | Check whether you are currently in the league in this channel |            |
| `/standings`                                                                | View the current standings                                    |            |
| `/report [tag opponent] [left player score] [right player score] [context]` | Report one of your matches                                    |            |
| `/results`                                                                  | Display the last round's results to everyone                  | x          |
| `/pair`                                                                     | Pair a new round                                              | x          |
| `/help`                                                                     | Show this command                                             |            |

Context is one of `241`, `id`, `runner split` (aliases: `runner`, `r`), `corp split` (aliases: `corp`, `c`)