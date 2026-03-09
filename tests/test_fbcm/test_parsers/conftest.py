import pytest
from bs4 import BeautifulSoup


@pytest.fixture
def make_soup():
    """Factory fixture that creates a BeautifulSoup object from an HTML string."""

    def _make_soup(html: str) -> BeautifulSoup:
        return BeautifulSoup(html, "html.parser")

    return _make_soup


# ---------------------------------------------------------------------------
# Shared HTML fragments used across multiple test modules
# ---------------------------------------------------------------------------

BASIC_INFO_HTML = """
<html><body>
<span class="player-info__first-name">Cam</span>
<span class="player-info__last-name">Ward</span>
<figure class="player-info__photo"><img src="/images/players/cam-ward.png"/></figure>
<div class="player-info-details">
  <div class="player-info-details__item">
    <h6 class="player-info-details__title">Height</h6>
    <div class="player-info-details__value">6-2</div>
  </div>
  <div class="player-info-details__item">
    <h6 class="player-info-details__title">Weight</h6>
    <div class="player-info-details__value">223</div>
  </div>
  <div class="player-info-details__item">
    <h6 class="player-info-details__title">College</h6>
    <div class="player-info-details__value">Miami</div>
  </div>
  <div class="player-info-details__item">
    <h6 class="player-info-details__title">Position</h6>
    <div class="player-info-details__value">QB</div>
  </div>
  <div class="player-info-details__item">
    <h6 class="player-info-details__title">Class</h6>
    <div class="player-info-details__value">Senior</div>
  </div>
  <div class="player-info-details__item">
    <h6 class="player-info-details__title">Home Town</h6>
    <div class="player-info-details__value">Columbia, SC</div>
  </div>
</div>
<table class="basicInfoTable">
  <tr><td>#1</td></tr>
  <tr>
    <td>
      <span title="Sub-Position">Sub-Position</span>
      <span>Pocket Passer</span>
    </td>
  </tr>
  <tr>
    <td>
      <span title="Last Updated">Last Updated</span>
      <span>2026-01-15</span>
    </td>
  </tr>
  <tr>
    <td>
      <span title="Draft Year">Draft Year</span>
      <span>2026</span>
    </td>
  </tr>
  <tr>
    <td>
      <span title="40 yard dash time">40 yard dash time</span>
      <span>4.65 seconds</span>
    </td>
  </tr>
</table>
</body></html>
"""

RATINGS_TABLE_HTML = """
<table class="starRatingTable">
  <tr>
    <th>Overall Rating</th>
    <td><span>92.5 / 100</span></td>
  </tr>
  <tr><td>filler row</td></tr>
  <tr>
    <td><div class="meter" title="Opposition Rating: 78%"></div></td>
  </tr>
  <tr><td>filler row 2</td></tr>
  <tr>
    <td>
      <span>Release Speed: 88/100</span>
    </td>
  </tr>
  <tr>
    <td>
      <span>Short Passing: 90/100</span>
    </td>
  </tr>
  <tr>
    <td>
      <span>Medium Passing: 85/100</span>
    </td>
  </tr>
  <tr>
    <td>
      <span>Long Passing: 82/100</span>
    </td>
  </tr>
  <tr>
    <td>
      <span>Rush Scramble: 75/100</span>
    </td>
  </tr>
  <tr>
    <td>
      <span>Draft Projection</span>
      <span>1st Round</span>
      <span>Overall Rank</span>
      <span>3</span>
      <span>Position Rank</span>
      <span>1</span>
    </td>
  </tr>
  <tr>
    <td>
      <span>ESPN Rating: 95/100</span>
    </td>
  </tr>
  <tr>
    <td>
      <span>Rivals Rating: 5.8</span>
    </td>
  </tr>
  <tr>
    <td>
      <span>247 RATING 0.99/1.0</span>
    </td>
  </tr>
</table>
"""


RANKING_BOX_HTML = """
<div class="rankingBox">
  <div class="rankVal">5.2</div>
  <div class="rankVal">2.1</div>
</div>
"""


SCOUTING_REPORT_HTML = """
<div class="playerDescIntro">Top quarterback prospect with elite arm talent.</div>
<div class="playerDescPro">
Scouting Report Strengths
Strong arm
Quick release
Good pocket presence
</div>
<div class="playerDescNeg">
Scouting Report Weaknesses
Footwork needs improvement
Tends to hold ball too long
</div>
<div class="playerDescNeg">Overall a very talented prospect with high upside.</div>
"""


COMPARISONS_TABLE_HTML = """
<table class="starRatingTable">
  <th>Comparisons</th>
  <tbody>
    <tr><td>Patrick Mahomes - Kansas City 92%</td></tr>
    <tr><td>Josh Allen - Buffalo 85%</td></tr>
  </tbody>
</table>
"""


QB_STATS_HTML = """
<html><body>
<span title="College Games Played">College Games Played</span>
<span>40</span>
<span title="College Snap Count">College Snap Count</span>
<span>2100</span>
<div id="QBstats">
  <table>
    <thead>
      <tr>
        <th class="player-season-avg__stat">Year</th>
        <th class="player-season-avg__stat">CMP</th>
        <th class="player-season-avg__stat">ATT</th>
        <th class="player-season-avg__stat">CMP%</th>
        <th class="player-season-avg__stat">YDS</th>
        <th class="player-season-avg__stat">TD</th>
        <th class="player-season-avg__stat">INT</th>
        <th class="player-season-avg__stat">SACK</th>
        <th class="player-season-avg__stat">Avg</th>
        <th class="player-season-avg__stat">Pro Rat</th>
        <th class="player-season-avg__stat">Rat</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>2024 Season</td>
        <td>280</td>
        <td>420</td>
        <td>66.7</td>
        <td>3800</td>
        <td>32</td>
        <td>8</td>
        <td>15</td>
        <td>9.0</td>
        <td>155.2</td>
        <td>92</td>
      </tr>
    </tbody>
  </table>
</div>
</body></html>
"""


DEFENSE_STATS_HTML = """
<html><body>
<span title="College Games Played">College Games Played</span>
<span>36</span>
<span title="College Snap Count">College Snap Count</span>
<span>1800</span>
<div id="DBLBDL-stats">
  <table>
    <thead>
      <tr>
        <th class="player-season-avg__stat">Year</th>
        <th class="player-season-avg__stat">Total</th>
        <th class="player-season-avg__stat">Solo</th>
        <th class="player-season-avg__stat">FF</th>
        <th class="player-season-avg__stat">Sacks</th>
        <th class="player-season-avg__stat">Ints</th>
        <th class="player-season-avg__stat">Yds</th>
        <th class="player-season-avg__stat">TD</th>
        <th class="player-season-avg__stat">PDs</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>2024 Season</td>
        <td>65</td>
        <td>42</td>
        <td>3</td>
        <td>8.5</td>
        <td>2</td>
        <td>35</td>
        <td>1</td>
        <td>10</td>
      </tr>
    </tbody>
  </table>
</div>
</body></html>
"""

RB_STATS_HTML = """
<html><body>
<span title="College Games Played">College Games Played</span>
<span>30</span>
<span title="College Snap Count">College Snap Count</span>
<span>1500</span>
<div id="RB-Rush-stats">
  <table>
    <thead>
      <tr>
        <th class="player-season-avg__stat">Year</th>
        <th class="player-season-avg__stat">ATT</th>
        <th class="player-season-avg__stat">YDS</th>
        <th class="player-season-avg__stat">AVG</th>
        <th class="player-season-avg__stat">TD</th>
        <th class="player-season-avg__stat">REC</th>
        <th class="player-season-avg__stat">REC YDS</th>
        <th class="player-season-avg__stat">REC AVG</th>
        <th class="player-season-avg__stat">REC TD</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>2024</td>
        <td>200</td>
        <td>1200</td>
        <td>6.0</td>
        <td>14</td>
        <td>30</td>
        <td>250</td>
        <td>8.3</td>
        <td>2</td>
      </tr>
    </tbody>
  </table>
</div>
</body></html>
"""
