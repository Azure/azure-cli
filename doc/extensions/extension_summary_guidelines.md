# Extension Summary Guidelines

Extension summaries are required to follow these rules in order to be published
on the documentation site:
 
1. Summaries must contain complete sentences.
2. Summaries must not be more than 3 sentences. Single sentences are preferred, 120-140 character max.
3. Summaries must use correct spelling and English grammar, including definite and indefinite articles for nouns ('the', 'a', or 'an')
4. Extension names are not proper nouns  (i.e. should be 'alias extension', not 'Alias Extension')
 
    BAD: Azure CLI Alias Extension  
    IMPROVED: The Azure CLI alias extension.
 
4. Summaries must provide a useful description.
 
    BAD: Azure IoT CLI Extension  
    IMPROVED: Additional IoT commands.
 
5. Summaries should not include the following language: 'An extension', 'Azure CLI', 'command-line', or other language that refers to the CLI product or the object being installed as an extension. These are implicit: You are finding the extensions either via `az extension` or directly on the Azure CLI documentation site.
 
    BAD: Azure CLI Alias Extension  
    IMPROVED: The Azure CLI alias extension.  
    BEST: Support for command aliases.
 
    BAD: An Azure CLI Extension that copies images from region to region.  
    IMPROVED: Support for copying images between regions.
 
6. Summaries must be as specific as possible. For example the term 'images' used in the examples for 5 is ambiguous. VM images? Container images?
 
7. Summaries which included branded product names should use the correct branding terminology and capitalization.
 
    BAD: Microsoft Azure Command-Line Tools Extended Batch Command Module  
    IMPROVED: Additional Azure Batch commands.
 
8. Provide an example (or examples) of the types of commands added or modified.
 
    BAD: Azure IoT CLI Extension  
    IMPROVED: Additional IoT commands.  
    BEST: Additional commands for working with IoT Hub, Edge, and device provisioning.
