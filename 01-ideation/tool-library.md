# Idea Canvas: Tool Library

## Date: 2026-11-28
## Author: Drafted by Claude for Ubay Gonzalez
## Status: Draft

> Sample product for a trial run of this template. Ubay gave the name only ("tool-library") and asked for the
> rest to be written for him (2026-11-28). Every figure below is an assumption to be replaced, not evidence.

---

## 1. Problem Statement
People who live in flats or small houses need a drill, a ladder or a tile cutter a few times a year. Buying
one costs 50 to 300 euros, takes storage space they don't have, and the tool then sits unused. Renting from a
hardware chain is priced by the day for trade use and means a deposit and a trip to an out-of-town store.
Neighbourhood associations that already lend tools informally track them in a paper notebook or a spreadsheet,
so tools go missing, come back broken without anyone knowing who had them, and are double-booked.

The people with the problem are residents who do occasional home repairs, and the volunteers who run a
lending point.

## 2. Target Market
- **Primary audience:** neighbourhood associations, housing cooperatives and municipal civic centres that run,
  or want to run, a tool lending point; and their members who borrow.
- **Market size (TAM/SAM/SOM):** assumption, not researched. TAM: every municipality and housing association
  in Spain (about 8,100 municipalities). SAM: urban districts above 20,000 residents with an active
  association (assumed 1,500). SOM in the first year: 20 lending points in one city.
- **Customer segments:** volunteer-run associations (no budget, need it simple); municipalities (pay, need
  reporting); housing cooperatives (closed membership).

## 3. Value Proposition
A lending point knows where every tool is, who has it and when it is due, without a volunteer keeping a
notebook. A member sees what is free this weekend and reserves it from a phone in under a minute. Compared
with a spreadsheet, nothing is double-booked and late returns are chased automatically. Compared with
commercial rental, it is local, cheap and aimed at one-off household jobs.

## 4. Proposed Solution
A web application, usable on a phone, with two sides:
- **Members:** browse the catalogue of one lending point, see availability by date, reserve, get reminders to
  collect and to return, report a fault.
- **Volunteers:** add tools with a photo and a label code, check a tool out and in by scanning the label,
  see what is overdue, mark a tool as broken or under repair, see a simple history per tool and per member.

One lending point per installation at first. No payments in the first version: membership fees and deposits
are handled by the association as they are today.

## 5. Revenue Model
- **Pricing strategy:** free for volunteer-run lending points up to 100 tools; a monthly fee for municipalities
  and for larger inventories.
- **Revenue streams:** subscriptions from municipalities and cooperatives (assumed 40 euros a month per
  lending point); later, an optional payments add-on for deposits and late fees.
- **Unit economics:** assumption. Hosting under 3 euros a month per lending point; support is the main cost.

## 6. Competitive Landscape
| Competitor | Strengths | Weaknesses | Our Differentiator |
|-----------|-----------|------------|-------------------|
| Spreadsheet or paper notebook | Free, already in use | Double bookings, no reminders, no history | Reservations and reminders with no extra work for volunteers |
| myTurn | Mature, built for tool libraries | Priced and designed for large US libraries, English first | Small lending points, Spanish and Catalan first, free tier |
| Hardware-chain rental | Wide range, professional tools | Daily trade prices, deposit, travel | Local and for occasional household use |
| Generic booking tools | Cheap, familiar | No inventory, condition or check-in/out | Built around the physical tool and its condition |

## 7. Key Assumptions
1. Associations will move off the notebook if adding a tool takes under two minutes.
2. Members will reserve ahead instead of turning up to ask.
3. Municipalities will pay for usage reporting on a service they already fund.
4. Volunteers have a phone that can scan a printed label.
5. Losses and damage fall when every loan has a name and a due date.

## 8. Design Partners / Client Evidence
- **Design partners consulted:** none yet.
- **Client feedback:** none yet.
- **Evidence status:** None yet

## 9. Success Metrics
- **North star metric:** loans completed and returned on time per lending point per month.
- **Leading indicators:** tools catalogued in the first week; share of loans that started as a reservation;
  members who borrow a second time within 60 days.
- **Lagging indicators:** tools lost or returned broken per 100 loans; lending points still active after six
  months; paying lending points.

## 10. High-Level Timeline
| Phase | Duration | Milestone |
|-------|----------|-----------|
| Discovery | 3 weeks | Interviews with five lending points; assumptions 1 to 3 tested |
| Pilot build | 8 weeks | Catalogue, reservations, check-out and check-in at one lending point |
| Pilot | 8 weeks | 100 loans through the application at the pilot lending point |
| Second release | 6 weeks | Reminders, fault reports, overdue list, three more lending points |

## 11. Initial Resource Estimate
- **Team:** one product owner part-time, one developer, a designer for two weeks.
- **Budget:** assumption, 25,000 euros to the end of the pilot.
- **Infrastructure:** one small hosted database and web service; an email sender for reminders.

## 12. Open Questions
- Who is liable when a borrowed tool injures someone, and does the application need to record a signed waiver?
- Which personal data of members is needed, and who is the data controller: the association or us?
- Are deposits and late fees needed in the first version for associations to adopt it?
- One city first, and which?
