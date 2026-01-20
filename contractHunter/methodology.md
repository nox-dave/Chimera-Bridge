"The Tincho"

Reconnaissance
We've finally scoped out our client's code base and we're ready to dive into looking more closely at the code.

To do this, we're going to learn some best practices and a technique I've dubbed The Tincho from the master himself - Tincho Abbate.

Introducing Tincho
Tincho is a legend in Web3 security and is a member of The Red Guild, a smart contract and EVM security firm. He was a previous lead auditor for the security firm at OpenZeppelin and he even helped me create this course!

We're lucky to have Tincho walk us through his high-level way to approach security reviews.

What follows is derived from a video featuring Tincho's point of view

The Tincho Auditing Method
To illustrate the Tincho auditing method, we're going to refer to a video where Tincho performs a live auditing of the Ethereum Name Service (ENS).

"I don't have a super formal auditing process. I will just show you briefly some things that I do..." - Tincho

First Step
First thing's first - download the code, and read the documentation. You need to familiarize yourself with the content and context of the codebase, learn the jargon you can expect to see in the code and become comfortable with what the protocol is expected to do.

READ THE DOCUMENTATION

Tools and Frameworks
Tincho describes a number of tools he uses while performing security reviews, bring the tools you're most familiar and best with.

VS Codeium: a text editor with a privacy focus. It's based on VS Code but removes a lot of the user tracking telemetry

Foundry: As a framework for reviewing codebases Foundry is incredibly fast and allows for quick testing with it's robust test suite

CLOC: A simple command-line utility that helps count lines of code which can give a sense of the complexity of different parts of the codebase.

Solidity Metric: Another tool developed by Consensys that provides useful metrics about your Solidity codebase.

By leveraging CLOC and Solidity Metrics, a security researcher can organize the codebase by complexity and systemically go through the contracts - marking them each complete as appropriate. This pragmatic approach ensures no stone is left unturned.

It's recommended to start with the smaller and more manageable contracts and build upon them as you go.

There's a point in an audit where your frame of mind should switch to an adversarial one. You should be thinking "How can I break this..."

tincho1

Given even simple functions like above, we should be asking ourselves

"Will this work for every type of token?"

"Have they implemented access control modifiers properly?"

USDT is a 'weird ERC20' in that it doesn't return a boolean on transferFrom calls

Audit, Review, Audit, Repeat
Keeping a record of your work is crucial in this process.

Tincho recommends taking notes directly in the code and maintaining a separate file for raw notes/ideas.

Remember, there is always a risk of diving too deep into just one part of the code and losing the big picture. So, remember to pop back up and keep an eye on the over-all review of the code base.

Not everything you'll be doing is a manual review. Applying your knowledge of writing tests to verify suspicions is incredibly valuable. Tincho applies a fuzz test to his assessment of functions within the ENS codebase.

Communication
Tincho describes keeping an open line of communication with the client/protocol as fundamental. The protocol is going to possess far more contextual understanding of what constitutes intended behavior than you will. Use them as collaborators. Trust but validate.

"I would advise to keep the clients at hand. Ask questions, but also be detached enough." - Tincho

Wrapping it Up
Sometimes it can feel like there's no end to the approaches you can make to a codebase, no end to the lines of code you can check and verify.

Tincho advocates for time-bounding yourself. Set limits and be as thorough as possible within them.

"The thing is...I always get the feeling that you can be looking at a system forever." - Tincho

The Audit Report and Follow Up
The last stage of this whole process is to present an audit report to the client. It should be clear and concise in the detailing of discovered vulnerabilities and provide recommendations on mitigation.

It's our responsibility as security researchers to review the implementation of any mitigations the client employs and to assure that new bugs aren't introduced.

Aftermath of a Missed Vulnerability
There will always be the fear of missing out on some vulnerabilities and instead of worrying about things that slip through the net, aim to bring value beyond just identifying vulnerabilities. Be that collaborative security partner/educator the protocol needs to employ best practices and be prepared holistically.

As an auditor it's important to remember that you do not shoulder the whole blame when exploits happen. You share this responsibility with the client.

This doesn't give you free reign to suck at your job. People will notice.

A last takeaway from Tincho:

"Knowing that you’re doing your best in that, knowing that you’re putting your best effort every day, growing your skills, learning grows an intuition and experience in you."

=======================================================================================================

First Step: Understanding The Codebase
Alright, we're ready to begin our recon, if you haven't already clone the repo our client has provided us.

git clone https://github.com/Cyfrin/3-passwordstore-audit.git
cd 3-passwordstore-audit
code .
If we're following The Tincho method, our first step is going to be reading the docs and familiarizing ourselves with the codebase. In VS Code, you can click on the README.MD file in your workspace and use the command CTRL + SHIFT + V to open the preview mode of this document.

You can also open the preview pane by opening your command pallet and typing markdown open preview.

Quick tip: Check if an extension must be installed for VS Code if it's not working for you.

context2

Already, we should be thinking about potential attack vectors with the information we've gleaned.

Is there any way for an unauthorized user to access a stored password?

Once you've finished reading through the documentation, we can proceed to...

Scoping Out The Files
Following Tincho's advice our next step will be to organize the files of the protocol in scope and assess their respective complexity. (Spoiler, this first example is pretty simple).

Download and install the Solidity Metrics extension for VS Code.

context3

Once installed, you can right-click the appropriate folders to run the tool on and select Solidity: Metrics from the context menu.

Pro-tip: If your repo has more than one applicable folder, you can CTRL + Click to select multiple simultaneously.

context4

After generating the report, navigate to the command palette and locate 'export this metrics report'. Once exported, you'll have HTML access to the report for future reference.

context5

Applying Tincho's methodology to this process, we can:

Scroll down to the section containing the various files and their lengths.

Copy this info and paste it onto any platform that allows for easy viewing and comparison— like Google Sheets or Notion.

Please note that if your codebase contains a solitary file like ours, this step won't be necessary.

Some aspects I'll draw your attention to in this metrics report are the Inheritance Graph, The Call Graph, and The Contracts Summary. It's not super obvious with such a simple protocol, but these are going to provide valuable insight down the line. Familiarize yourself with them now (way at the bottom).

context6

Understanding your codebase and its functionalities is the first step towards securing it.

Wrap Up
Now that we've got a sense of what lies before us, with the help of our tools like CLOC and Solidity Metrics, we're ready to assess the code.

Let's see what we can find.

=====================================================================================================

