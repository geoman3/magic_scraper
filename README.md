# Magic the Scrapening

Hey!

This is a small project for making a model for recognising / identifying cards from Wizards of the Coast's (WotC, I pronounce it "Wotzee") card game Magic the Gathering, the TCGPlayer app already does this but I find it a bit hard to use if I just want to scan my trade binder to catalogue my collection.

## TO DO

1. Parse the type line for {(supertypes) (type) - (subtypes) (P/T or Loyalty)} - done

2. Download card images - in progress

3. define model problem

4. train model - might go back and forth between 3 / 4 a lot

## DEV LOG

2021/07/28

The initial scraping script wasnt too difficult as WotC provide a complete list of all of the cards at "https://gatherer.wizards.com/Pages/Search/Default.aspx?name=+[]" (paginated of course) in a fairly consistent format. I only had a bit of trouble parsing the data from the typeline so when I first downloaded it I left the string unprocessed

2021/07/30

After spending the day struggling with regex trying to get the types / supertypes / subtypes from the typeline I gave up and chained a few str.split and if / else statements to get the job done - that was not very regex - cellent of me

2021/07/30

I now need to go about downloading each of the cards' images, each card has 1 or more editions each with their own multiverse id that is used in the image url making the image scraping script a cinch. However upon further inspection, some cards have other versions with their own multiverse id that are not displayed on the main gatherer search page under `Other Versions`, see "https://gatherer.wizards.com/Pages/Card/Details.aspx?multiverseid=3012" and click `Other Variations` underneath the card image. Im hoping this won't be a big deal as it seems to be fairly uncommon.

2021/08/01

I saw this "https://tmikonen.github.io/quantitatively/2020-01-01-magic-card-detector/" blog and Im gonna give it a go, this person wisely used a perceptual hash instead of employing a model given we have an exact copy of the objects we are trying to identify, saving on the need to do any sort of machine learning. However they only tested it on a particular set of 290 cards (alpha), Im now gonna see if this method extends to the full collection of ~23 000.