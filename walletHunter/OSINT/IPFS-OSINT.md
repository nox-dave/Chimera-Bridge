What is IPFS?
IPFS (InterPlanetary File System) is decentralized file storage used heavily in Web3. When you see an NFT image, metadata, or dApp frontend - it's often hosted on IPFS, not a normal server.
Why does IPFS matter for OSINT?
Traditional WebIPFS/Web3Files on servers you can traceFiles distributed across nodesDomain → IP → OwnerContent hash → ???Takedowns workContent persists even after "deletion"Centralized hostingDecentralized, harder to trace
How it relates to your work:

NFT metadata lives on IPFS - When you profile an NFT collector in Gargophias, their PFP/metadata is on IPFS. You can pull that data, analyze it, potentially find info the owner thought was hidden.
Malicious content distribution - Phishing sites, malware, scam contracts often host frontends on IPFS because it's censorship-resistant. Tracing this = finding attackers.
Evidence that doesn't disappear - Unlike a deleted tweet, IPFS content can persist. Good for investigations.
Data leaks - IPFS scanning can identify new hosted content or expose information leaks similar to Amazon S3 buckets. GitHub

Connection to your categories:
Your Gargophias target is a 🏆_status_seeker (NFT collector)
    → Their NFT metadata is on IPFS
    → IPFS OSINT can reveal: upload timestamps, linked content, 
      potentially misconfigured data exposing identity
Bottom line: It's a Web3-specific OSINT technique. Traditional OSINT = websites, social media. Web3 OSINT = on-chain data + IPFS. This video fills that gap.