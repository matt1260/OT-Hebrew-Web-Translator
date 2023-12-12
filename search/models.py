from django.db import models

# Django genesis database 
class Genesis(models.Model):
    
    id = models.AutoField(primary_key=True)
    chapter = models.IntegerField()
    verse = models.IntegerField()
    html = models.TextField()
    text = models.TextField()
    hebrew = models.TextField()
    rbt_reader = models.TextField()
    
    class Meta:
        db_table = 'genesis'

    def __str__(self):
        return f"Chapter {self.chapter}, Verse {self.verse}"
    
class EngLXX(models.Model):
    
    verseID = models.AutoField(primary_key=True)
    canon_order = models.TextField()
    book = models.TextField()
    chapter = models.TextField()
    startVerse = models.TextField()
    endVerse = models.TextField()
    verseText = models.TextField()

    class Meta:
        db_table = 'englxxup'

    def __str__(self):
        return f"Book {self.book}, Chapter {self.chapter}, Verse {self.startVerse}"

class LITV(models.Model):
    
    id = models.AutoField(primary_key=True)
    book = models.TextField()
    chapter = models.TextField()
    verse = models.TextField()
    text = models.TextField()

    class Meta:
        db_table = 'litv'

    def __str__(self):
        return f"Book {self.book}, Chapter {self.chapter}, Verse {self.verse}"
    
# Django genesis footnotes database 
class GenesisFootnotes(models.Model):
    
    id = models.AutoField(primary_key=True)
    footnote_id = models.TextField()
    footnote_html = models.TextField()
    original_footnotes_html = models.TextField()
    
    class Meta:
        db_table = 'genesis_footnotes'

    def __str__(self):
        return f"Footnote ID {self.footnote_id}, Footnote {self.footnote_html}"