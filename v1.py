
def get_number(word):
    has_number = False #used to check if the word has a number
    number = "" #used to store the number if it is found
    for char in word: #iterate through each character in the word
        if char.isdigit(): #check if the character is a digit
            number += char  #add the digit to the number so that if it is a multi-digit number it will be stored correctly
            has_number = True #set has_number to True because a number was found
    return has_number, number #return the values of has_number and number so that they can be used later in the code

def seperate_vocab(vocab):
    v_word_and_def = {} #used to store the vocab words and definitions
    vocab_word = "" #used to store the vocab word
    vocab_words = [] #used to store the vocab words
    vocab_def = "" #used to store the definition of the vocab word
    vocab_def_list = [] #used to store the definitions of the vocab words
    hi = 0 #used later 
    for word in vocab.split(): #split input into lsit of words
        #print(word) #print the word

        if word == "-": #check if the word is a dash meaning that it stops the word and starts the definition
                    hi = 2 #set hi to 2 to store the next words as vocab_def
                    #print("hi is 2")
                    vocab_words.append(vocab_word) #add the vocab word to the list of vocab words
                    vocab_word = "" #reset vocab_word to store the next vocab word

        if hi == 1: #checks if the last run set hi as 1
            vocab_word += word + " " #store the word
            #hi = 0 #reset hi  #commented out because some r more than one word long

        if hi == 2: #checks if the last run set hi as 2
            vocab_def += word + " " #add the word to the definition
            hi = 2 #keep hi as 2 to keep adding words to the definition
            #print(vocab_def)

        has_number, number = get_number(word) # gets the value of get_number fnc to check if there is a number and if so what is it so that it can be removed from the definition later because it look werid otherwise so i did more code jsut to remove a single character becuase y be good when you could be great like tony the tiger from dat one cerial box brand (holy yap)
        #print(has_number, number) #print the values of has_number and number to check if they are correct

        if has_number: #check if theres a number
            hi = 1 #set hi to 1 to store the next word as vocab_word
            if vocab_def != "": #check if the definition is not empty
                vocab_def_list.append(vocab_def.replace(number, "")) #add the definition to the list of definitions and remove the number from the definition 
                vocab_def = "" #reset the definition to store the next definition

    vocab_def_list.append(vocab_def) #add the last definition to the list of definitions because the loop ends before it can be added


    #print("\n\n" + str(vocab_words)) #print the vocab word
    #print("\n" + str(vocab_def_list)) #print the vocab definitions
    for i, j in zip(vocab_words, vocab_def_list): #iterate through the vocab words and definitions
        v_word_and_def[i.strip()] = j.strip()  #add the vocab word and definition to the string to be printed later
    return v_word_and_def #return the string of vocab words and definitions
            


if __name__ == "__main__":
    test_input = "6.      Parietal Lobe - A major sensory processing hub for your brain. It processes information about temperature, taste, touch and movement7.      Lobotomy - A surgical procedure in which the nerve pathways in a lobe or lobes of the brain are severed from those in other areas."
    #above used for testing, i put it above so that i dont have to comment the damn lines every single time i want to test it and can just press enter to use test input becuase i am lazy and dont want to type it out every time i want to test it 
    vocab = input("Enter the vocabulary (each word starting with number and - between word and definition): ") #get input
    #print(vocab)
    hello = seperate_vocab(vocab if vocab != "" else test_input) #call the function to seperate the vocab and definitions also check if the input is empty and if so use the test input instead so that i dont have to type it out every time i want to test it or comment out the lines cuz thats anoying and im lazy
    #print(hello) #print the vocab words and definitions
    """for word, definition in hello.items(): #iterate through the vocab words and definitions
        print(f"\n{word} - {definition}") #print the vocab word and definition"""


