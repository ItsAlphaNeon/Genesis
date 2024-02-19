from openai import AsyncOpenAI
import json
import os
import emoji as emoji



def get_openai_key():
    # Get the OpenAI key from the text file
    if not os.path.isfile("openai_key.txt"):
        file = open("openai_key.txt", "w")
        file.write("YOUR_OPENAI_KEY")
        file.close()
        print("Please add your OpenAI key to openai_key.txt")
        exit()

    with open("openai_key.txt", "r") as file:
        key = file.read()
        return key
    
def get_mix_key():
    # Get the mix key from the text file
    if not os.path.isfile("mix_key.txt"):
        file = open("mix_key.txt", "w")
        file.write("YOUR_MIX_KEY")
        file.close()
        print("Please add your Mix key to mix_key.txt")
        exit()

    with open("mix_key.txt", "r") as file:
        key = file.read()
        return key


def process_emojis(emoji_text):
    ## Multiple emoji processing. This is disabled for now
    # str_emoji = str(emoji_text)
    # print(str_emoji)
    # emojis = []
    # print("Emojis array is " + str(emojis))
    # final_string = ""
    # for i, char in enumerate(str_emoji):
    #     uni_char = '{:X}'.format(ord(char))
    #     final_string += uni_char
    #     if i < len(str_emoji) - 1:
    #         final_string += "%"  # Separator

    # print(f"Final String: {final_string}")
    
    ## Temporary multiple to single emoji processing
    inputstr = str(emoji_text)
    final_string = ""
    # get the first emoji
    char = inputstr[0]
    uni_char = '{:X}'.format(ord(char))
    final_string += uni_char
    return final_string

def process_mix_emojis(list_emojis, best_emoji):
    print("Processing Emojis")

client = AsyncOpenAI(api_key=get_openai_key())
mix_client = AsyncOpenAI(api_key=get_mix_key(), base_url="https://api.together.xyz/v1")


async def ai_combine_terms(term1, term2):
    messages = [
        {
            "role": "system",
            "content": """
            You are Genesis, an AI who can combine two elements to create a new one. Similar to an elment-combining game, you can combine two elements to create a new one. Think in this mindset.
            
            For example, if are told to combine "Fire" and "Water", you should respond with "Steam".
            
            Try to be as realistic as possible, and create logical results. Try to create real elements, compounds, or concepts.
            
            If you feel that the combination can't possibly result in anything new, You can respond with one of the original terms. 
            However, some terms may benefit from being the same, such as "Water" and "Water", which could result in "Ocean", or "Air and Air", which could result in "Pressure".
            
            Create Nouns primarily, but you can create Verbs and Adjectives if needed. Keep it to 1 word responses if possiblie. Only respond with known existing elements, compounds, or concepts.
            
            Respond with a json object containing 4 parts:
            
            1. A brief explanation of the combination and why you chose the result. Keep this 1 sentance long, and keep it very simple.
            2. The result of the combination. Keep it proper and capitalize the first letter.
            3. An emoji that best represents the result. Use unicode emojis. If none make sense, pick whatever relates closest. ALWAYS RETURN AN EMOJI
            4. A general color that represents the result. If none make sense, pick whatever. Tell me it in hex format like this: #000000 Do not do this: #Black
            
            Use this schema:
            {
                "explanation": "The explanation",
                "result": "The result",
                "emoji": "🔥",
                "color": "#000000"
            }
            This will be parsed by the server, so ONLY respond with a json object.
            """,
        },
        {"role": "user", "content": "Combine {} and {}".format(term1, term2)},
    ]

    valid = False
    while not valid:
        completion = await client.chat.completions.create(
            model="gpt-3.5-turbo", messages=messages
        )

        # Make sure the response is valid JSON and retry if not
        try:
            json.loads(completion.choices[0].message.content)
            emoji = json.loads(completion.choices[0].message.content)["emoji"]
            if emoji == "":
                print("No emoji provided. Re-trying")
                continue
            valid = True
        except json.JSONDecodeError:
            print("Invalid response from AI")
            print("Re-trying")

    print(completion.choices[0].message.content)
    # jsonify so we can access the emoji
    parsed_result = json.loads(completion.choices[0].message.content)
    print(parsed_result)
    emoji_text = parsed_result["emoji"]
    print(emoji_text)

    # Process the emojis
    processed_emoji = process_emojis(emoji_text)
    print(processed_emoji)
    
    # Replace the emoji with the unicode name
    parsed_result["emoji"] = processed_emoji
    print(parsed_result)
    return parsed_result

async def ai_combine_terms_mix(term1, term2):
    messages = [
        {
            "role": "system",
            "content": """You are Genesis, an AI who can combine two elements to create a new one. Similar to an element-combining game, you can combine two elements to create a new one. Think of this as a video game. For example, if are told to combine "Fire" and "Water", you should respond with "Steam". Try to be as realistic as possible, and create logical results. Try to create real elements, compounds, or concepts. Avoid using the terms "Ultra, Mega, Super" etc. in your results. If you feel that the combination can't possibly result in anything new, You can respond with one of the original terms. However, some terms may benefit from being the same, such as "Water" and "Water", which could result in "Ocean", or "Air and Air", which could result in "Pressure". Create Nouns primarily, but you can create Verbs and Adjectives if needed. Keep it to 1 word responses if possible. Only respond with known existing elements, compounds, or concepts. Respond with a JSON object containing 4 parts: Explanation: A brief explanation of the combination and why you chose the result. Keep this 1 sentence long, and keep it very simple. Result: The result of the combination. Keep it proper and capitalize the first letter. List of Emojis: A list of 10 related emojis to the result.Best Emoji: A single Emoji that you feel is the best fit from the previous list. Color: A general color that relates to the result. If none make sense, pick whatever. Tell me it in hex format like this: #000000 Do not do this: #Black.  Use this schema: {"explanation":"{The explanation}","result":"{The result}","list_emojis":"{list_of_emojis}","best_emoji":"{best_emoji},"color": "{#000000}"}  This will be parsed by the server, so ONLY respond with a JSON object. Your response should begin and end with { and }
            """,
        },
        {"role": "user", "content": "Combine {} and {}".format(term1, term2)},
    ]

    MAX_RETRIES = 5
    retry_count = 0
    
    valid = False
    while not valid:
        if retry_count >= MAX_RETRIES:
            print("Max retries reached. Exiting.")
            break

        try:
            completion = await mix_client.chat.completions.create(
                model="mistralai/Mixtral-8x7B-Instruct-v0.1", messages=messages
            )

            # Attempt to parse the JSON response once
            response_content = json.loads(completion.choices[0].message.content)

            # Use the parsed content to check for the 'emoji' key
            emoji = response_content.get("list_emojis", "")  # Use .get to handle missing key gracefully
            if emoji == "":
                print("No emoji provided. Re-trying")
                retry_count += 1
                continue

            valid = True
        except json.JSONDecodeError:
            print("Invalid response from AI")
            print("Re-trying")
            retry_count += 1

    print(completion.choices[0].message.content)
    # jsonify so we can access the emoji
    parsed_result = json.loads(completion.choices[0].message.content)
    print(parsed_result)
    list_emojis = parsed_result["list_emojis"]
    best_emoji = parsed_result["best_emoji"]
    print(list_emojis)
    print(best_emoji)

    # Process the emojis
    processed_emoji = process_mix_emojis(list_emojis, best_emoji)
    print(processed_emoji)
    
    # Replace the emoji with the unicode name
    parsed_result["emoji"] = "null"
    print(parsed_result)
    return parsed_result


if __name__ == "__main__":
    # print("Wrong file to run. Run main.py instead")
    # exit()
    
    emojitest = process_emojis("🔥")
    print(emojitest)