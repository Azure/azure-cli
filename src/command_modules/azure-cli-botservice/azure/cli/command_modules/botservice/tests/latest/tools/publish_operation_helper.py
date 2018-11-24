# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


class BotDownloadHelper:

    @staticmethod
    def overwrite_v4_node_bot_js(bot_js_path):
        """Overwrites v4 Node.js bot for live testing the publish operation.

        Takes a string path to the bot.js file in question and opens it before writing over its contents.

        :param bot_js_path: string
        :return:
        """
        with open(bot_js_path, 'w') as bot:
            bot.write("""
            // Copyright (c) Microsoft Corporation. All rights reserved.
            // Licensed under the MIT License.

            // bot.js is your bot's main entry point to handle incoming activities.
            const { ActivityTypes } = require('botbuilder');

            // Turn counter property
            const TURN_COUNTER_PROPERTY = 'turnCounterProperty';
            class EchoBot {
                /**
                *
                * @param {ConversationState} conversation state object
                */
                constructor(conversationState) {
                    // Creates a new state accessor property.
                    // See https://aka.ms/about-bot-state-accessors to learn more about the bot state and state accessors
                    this.countProperty = conversationState.createProperty(TURN_COUNTER_PROPERTY);
                    this.conversationState = conversationState;
                }
                /**
                *
                * Use onTurn to handle an incoming activity, received from a user, process it, and reply as needed
                *
                * @param {TurnContext} on turn context object.
                */
                async onTurn(turnContext) {
                    // Handle message activity type. User's responses via text or speech or card interactions flow back to the bot as Message activity.
                    // Message activities may contain text, speech, interactive cards, and binary or unknown attachments.
                    // see https://aka.ms/about-bot-activity-message to learn more about the message and other activity types
                    if (turnContext.activity.type === ActivityTypes.Message) {
                        // read from state.
                        let count = await this.countProperty.get(turnContext);
                        count = count === undefined ? 1 : ++count;
                        await turnContext.sendActivity(`${ count }: You said "${ turnContext.activity.text }"`);
                        await turnContext.sendActivity('That was awesome!');
                        // increment and set turn counter.
                        await this.countProperty.set(turnContext, count);
                    } else { 
                        // Generic handler for all other activity types.
                        await turnContext.sendActivity(`[${ turnContext.activity.type } event detected]`);
                        await turnContext.sendActivity('(Try sending a message to me!)');
                    }
                        // Save state changes
                        await this.conversationState.saveChanges(turnContext);
                }
            }
            exports.EchoBot = EchoBot;""")
            bot.close()
