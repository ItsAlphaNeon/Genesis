import json
import asyncio
import requests
import random
import os
from gpt import ai_combine_terms, get_openai_key, ai_combine_terms_training

global element_bank  # This holds a list of all the elements that have been created so far

async def main():
    for i in range(5):
        word1 = get_word()
        word2 = get_word()
        
        test_prompt = await ai_combine_terms_training(word1, word2)
        
        print(test_prompt[0])
        print(test_prompt[1])
        
        with open("training_data.txt", "a", encoding='utf-8') as file:
            json.dump({"prompt": test_prompt[0]}, file)
            file.write("\n")
            
        print("Training data written")
        
        # Add the new element to the element bank (test_prompt[1])
        # Make sure its not already in the element bank
        
        if test_prompt[1] not in element_bank:
            element_bank.append(test_prompt[1])
            with open("elements.txt", "a", encoding='utf-8') as file:
                json.dump({"element": test_prompt[1]}, file)
                file.write("\n")
            print("Element added to element bank")
        else:
            print("Element already in element bank")
            
def check_if_elements_exist():
    if not os.path.isfile("elements.txt"):
        with open("elements.txt", "w") as file:
            json.dump({"elements": ["Water", "Fire", "Air", "Earth"]}, file)
            
    elif os.path.isfile("elements.txt"):
        with open("elements.txt", "r") as file:
            data = json.load(file)
            if not data["elements"]:
                with open("elements.txt", "w") as file:
                    json.dump({"elements": ["Water", "Fire", "Air", "Earth"]}, file)
    else:
        print("Elements exist")
            
def pull_elements():
    global element_bank
    # Pull the list of elements from the json file "elements.json"
    with open("elements.txt", "r") as file:
        data = json.load(file)
        element_bank = data["elements"]


def get_word():
    # Get a random word from the element bank
    word = element_bank[random.randint(0, len(element_bank) - 1)]
    return word
    
if __name__ == "__main__":
    get_openai_key()
    
    check_if_elements_exist()
    
    pull_elements()
        
    asyncio.run(main())