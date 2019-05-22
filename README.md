# data-processing
Data processing scripts

1) python3 extract_all.py /home/mikkos/arkistosiirto* > stt_full_news_archive.jsonl

2) python3 align_documents.py --json stt_full_news_archive.jsonl (creates aligned_documents.json)

3) python3 hockey_events.py --json aligned_documents.json --known_teams teams_curated.txt --output hockey-events.txt (creates hockey-events.txt and hockey-events.json)

4) python3 join_annotations.py hockey-events.json hockey-events.txt annotated-hockey-events.json



jsonl2plaintext.py --> creates plain text input for the parser (not part of the actual generation data pipeline)
