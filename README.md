# Chapterize-Whisper

_A utility written to help get better chapters for Audiobookshelf_ 

Uses whisper and will make some automatic stuff

Batch mode is faster - but - it seems to give worse results for chapterfinding - so we use a slower option.

To install globally I think you can use:

```bash
pip install -U chapterize-whisper
chapterize --help
```


# Example

Download a free audiobook like this one:

https://librivox.org/the-adventures-of-danny-meadow-mouse-by-thornton-w-burgess/

and put it in some directory. Then we can use the `chapterize` command like:

```bash
chapterize detect --dir ./audio/danny_meadow_mouse_1301_librivox        
```

It will run a transcription process looking like this maybe:

![transscribe](docs/transcribe.jpg)

Once done you'll get a `.chapter` file in the directory of your audio files. For example this is what came out:

```
00:00:00,0000, BOOK Start
00:01:05,920,  Chapter 1, Danny Meadow Mouse is worried.
00:04:48,160,  Chapter two, Danny Meadow Mouse and his short tail.
00:08:06,120,  Chapter 3, Danny Meadow Mouse plays hide and seek.
00:13:04,759,  Chapter four, old Granny Fox tries for Danny Meadow Mouse.
00:17:17,137,  Chapter 5.
00:26:13,777,  Chapter seven, old Granny Fox tries a new plan.
00:30:15,497,  Chapter 8 Brother Northwind proves a friend.
00:35:00,017,  chapter 9, Danny Meadowmouse's caught at last.
00:39:38,975,  CHAPTER X
00:44:43,015,  Chapter 11, Peter Rabbit gets a fright.
00:48:35,415,  Chapter 12, the old briar patch has a new tenet.
00:52:44,135,  Chapter 13.
00:56:40,975,  Chapter 14, Farmer Brown sets a trap.
01:01:25,957,  Chapter 15 Peter Rabbit is caught in a snare.
01:05:32,077,  Chapter 16 Peter Rabbit's hard journey.
01:07:05,957,  Part of the stake to which the snare had been fastened and which Peter had managed to
01:10:10,397,  Chapter 17 Danny meadow mouse becomes worried.
01:15:02,917,  Chapter 18, Danny meadow mouse returns a kindness.
01:19:15,077,  Chapter 19, Peter Rabbit and Danny Meadowmouse live high.
01:23:41,237,  Chapter 20.
01:28:46,237,  Chapter 21, an exciting day for Danny Meadow Mouse.
01:33:23,997,  Chapter 22
01:41:31,997,  Chapter 24
01:46:18,820, BOOK_END

```

You'll notice some chapters are missing a full description - and some are wrong such as:
`00:27:43,702,  Part of the stake to which the snare had been fastened and which Peter had managed to`

For example to fix `Chapter 5.` open up the `.srt` file and look for where chapter 5 is:

```srt
318
00:17:17,137 --> 00:17:18,977
Chapter 5.

319
00:17:18,977 --> 00:17:22,137
What Happened on the Green Meadows
```

In this case we can assume the correct title is:

`Chapter 5. What Happened on the Green Meadows`


Also chapter 6 is missing - you can see in the srt it is here:

```srt
373
00:21:39,017 --> 00:21:48,497
End of Chapter 5 Chapter 6 Danny Meadow Mouse remembers, and ready Fox, poor kids.
```
This chapter will likely take some tweaking since you need to figure out how long the "End of Chapter 5" takes ... but you can also just guess - lets say 2 seconds. So you'd add this to the chapter file:

```
00:21:41, Chapter 6 Danny Meadow Mouse remembers
```

Once you've cleaned up the chapter files it will look like something like this. Maybe you are too lazy and don't want to fill out all the chapter titles - thats fine.


```
00:00:00,0000, BOOK Start
00:01:05,920,  Chapter 1, Danny Meadow Mouse is worried.
00:04:48,160,  Chapter two, Danny Meadow Mouse and his short tail.
00:08:06,120,  Chapter 3, Danny Meadow Mouse plays hide and seek.
00:13:04,759,  Chapter four, old Granny Fox tries for Danny Meadow Mouse.
00:17:17,137,  Chapter 5.
00:21:40,000,  Chapter 6.
00:26:13,777,  Chapter 7, old Granny Fox tries a new plan.
00:30:15,497,  Chapter 8 Brother Northwind proves a friend.
00:35:00,017,  chapter 9, Danny Meadowmouse's caught at last.
00:39:38,975,  CHAPTER 10
00:44:43,015,  Chapter 11, Peter Rabbit gets a fright.
00:48:35,415,  Chapter 12, the old briar patch has a new tenet.
00:52:44,135,  Chapter 13.
00:56:40,975,  Chapter 14, Farmer Brown sets a trap.
01:01:25,957,  Chapter 15 Peter Rabbit is caught in a snare.
01:05:32,077,  Chapter 16 Peter Rabbit's hard journey.
01:10:10,397,  Chapter 17 Danny meadow mouse becomes worried.
01:15:02,917,  Chapter 18, Danny meadow mouse returns a kindness.
01:19:15,077,  Chapter 19, Peter Rabbit and Danny Meadowmouse live high.
01:23:41,237,  Chapter 20.
01:28:46,237,  Chapter 21, an exciting day for Danny Meadow Mouse.
01:33:23,997,  Chapter 22
01:41:31,997,  Chapter 24
01:46:18,820, BOOK_END
```

The next step would be to upload this "chapter definition" to audiobook shelf.

First we need to upload this audiobook itself to Audiobookshelf - and as you can see - it doesnt have any chapter data

![image1](./docs/pre-chapters.jpg)

If you look at Audiobookshelf's URL you'll see something like this:

`https://audiobookshelf.local/item/2b1a5c2f-02e4-47bb-99ab-cc800aeafec7`

What we care about is the UUID for the item:

`2b1a5c2f-02e4-47bb-99ab-cc800aeafec7`

So with this information we can do the following:


```bash

 chapterize upload \
   --dir ./audio/danny_meadow_mouse_1301_librivox \
   --id 2b1a5c2f-02e4-47bb-99ab-cc800aeafec7  \
   --abs-url https://audiobookshelf.local \
   --api-key this-is-a-fake-api-key
```


[//]: # (### Uploading chapter data)

[//]: # ()
[//]: # (Next we will use the API https://api.audiobookshelf.org/#book-chapter to turn our .chapter_xxx file into an array of `book chapters` which can be uploaded to audiobookshelf)

[//]: # ()
[//]: # (and when we are done it looks like this:)

![done](docs/post-chapters.jpg)