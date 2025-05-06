# Somesite I Used to Crawl (IMC 25) Artifacts
This repository contains artifacts for for our IMC 25 paper ["Somesite I Used to Crawl"](https://arxiv.org/pdf/2411.15091). 
It includes code that parses robots.txt and data supporting our analysis on robots.txt adoption, web crawlers' behaviors, and active blocking.

## Repository Structure
* `robotstxt-parser/` contains our wrapper for Google's robots.txt parser and interpreting the results of their parser.
* `historical-analysis/` contains code and data related to Section 3 of the paper (longitudinal analysis on the adoption of robots.txt).
* `respect-robots-txt/` contains code and data related to Section 5 of the paper (whether AI crawlers respect robots.txt) as well as a bonus experiment on Perplexity-User conducted after the paper is accepted.
* `active-blocking/` contains code and data related to Section 6 of the paper (deployment of active blocking).


## Python version
Tested on Python 3.10.

## Report Issues
Please report any issues through Github Issues or email us directly :)

## Notes
For automated interaction with ChatGPT's web interface, we used [this repository](https://github.com/Michelangelo27/chatgpt_selenium_automation). Other similar projects exist (e.g., [this](https://github.com/iamseyedalipro/ChatGPTAutomation)).

## Citation
```bib
@inproceedings{liu2025somesite,
  title={Somesite I Used To Crawl: Awareness, Agency and Efficacy in Protecting Content Creators From AI Crawlers},
  author={Liu, Enze and Luo, Elisa and Shan, Shawn and Voelker, Geoffrey M and Zhao, Ben Y and Savage, Stefan},
  booktitle={Proceedings of the 2025 ACM Internet Measurement Conference (IMC 25)},
  year={2025}
}
```
