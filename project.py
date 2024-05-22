from datetime import datetime

class NewsStory:
    def __init__(self, guid, title, description, link, pubdate):
        self.guid = guid
        self.title = title
        self.description = description
        self.link = link
        self.pubdate = pubdate

    def get_guid(self):
        return self.guid

    def get_title(self):
        return self.title

    def get_description(self):
        return self.description

    def get_link(self):
        return self.link

    def get_pubdate(self):
        return self.pubdate

class Trigger:
    def evaluate(self, story):
        raise NotImplementedError

import string

class PhraseTrigger(Trigger):
    def __init__(self, phrase):
        self.phrase = phrase.lower()

    def is_phrase_in(self, text):
        text = text.lower()
        for p in string.punctuation:
            text = text.replace(p, ' ')
        words = text.split()
        phrase_words = self.phrase.split()
        for i in range(len(words) - len(phrase_words) + 1):
            if phrase_words == words[i:i+len(phrase_words)]:
                return True
        return False

class TitleTrigger(PhraseTrigger):
    def evaluate(self, story):
        return self.is_phrase_in(story.get_title())

class DescriptionTrigger(PhraseTrigger):
    def evaluate(self, story):
        return self.is_phrase_in(story.get_description())

class TimeTrigger(Trigger):
    def __init__(self, time_str):
        self.time = datetime.strptime(time_str, "%d %b %Y %H:%M:%S")

class BeforeTrigger(TimeTrigger):
    def evaluate(self, story):
        return story.get_pubdate() < self.time

class AfterTrigger(TimeTrigger):
    def evaluate(self, story):
        return story.get_pubdate() > self.time
class NotTrigger(Trigger):
    def __init__(self, trigger):
        self.trigger = trigger

    def evaluate(self, story):
        return not self.trigger.evaluate(story)

class AndTrigger(Trigger):
    def __init__(self, trigger1, trigger2):
        self.trigger1 = trigger1
        self.trigger2 = trigger2

    def evaluate(self, story):
        return self.trigger1.evaluate(story) and self.trigger2.evaluate(story)

class OrTrigger(Trigger):
    def __init__(self, trigger1, trigger2):
        self.trigger1 = trigger1
        self.trigger2 = trigger2

    def evaluate(self, story):
        return self.trigger1.evaluate(story) or self.trigger2.evaluate(story)

def filter_stories(stories, triggerlist):
    return [story for story in stories if any(trigger.evaluate(story) for trigger in triggerlist)]

def read_trigger_config(filename):
    trigger_map = {}
    trigger_list = []
    
    with open(filename, 'r') as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith('//'):
                continue

            parts = line.split(',')
            if parts[0] == 'ADD':
                trigger_list.extend(trigger_map[part] for part in parts[1:])
            else:
                name, trigger_type = parts[0], parts[1]
                if trigger_type == 'TITLE':
                    trigger = TitleTrigger(parts[2])
                elif trigger_type == 'DESCRIPTION':
                    trigger = DescriptionTrigger(parts[2])
                elif trigger_type == 'BEFORE':
                    trigger = BeforeTrigger(parts[2])
                elif trigger_type == 'AFTER':
                    trigger = AfterTrigger(parts[2])
                elif trigger_type == 'NOT':
                    trigger = NotTrigger(trigger_map[parts[2]])
                elif trigger_type == 'AND':
                    trigger = AndTrigger(trigger_map[parts[2]], trigger_map[parts[3]])
                elif trigger_type == 'OR':
                    trigger = OrTrigger(trigger_map[parts[2]], trigger_map[parts[3]])
                trigger_map[name] = trigger
                
    return trigger_list

import time
import feedparser
from project_util import translate_html

def main_thread(p):
    # Polling interval in seconds
    SLEEP_TIME = 120

    triggerlist = read_trigger_config("triggers.txt")

    while True:
        print("Polling...")
        stories = []
        # Fetching stories from RSS feeds
        feed = feedparser.parse("http://news.google.com/?output=rss")
        for entry in feed.entries:
            guid = entry.id
            title = translate_html(entry.title)
            description = translate_html(entry.description)
            link = entry.link
            pubdate = datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S %Z')
            stories.append(NewsStory(guid, title, description, link, pubdate))
        
        # Filter stories
        filtered_stories = filter_stories(stories, triggerlist)
        
        # Display filtered stories
        for story in filtered_stories:
            print(story.get_title())
            print(story.get_description())
            print(story.get_link())
            print()

        time.sleep(SLEEP_TIME)

if __name__ == '__main__':
    main_thread(None)


