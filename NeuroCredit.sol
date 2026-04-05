// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * NeuroCredit — Soul Bound Token (ERC-5484)
 * Non-transferable credit score NFT on Polygon
 *
 * Key properties:
 *  - One token per wallet address
 *  - Score updatable only by authorized issuer (backend oracle)
 *  - Transfer locked permanently
 *  - Score readable by anyone (lender verification)
 */

interface IERC5484 {
    enum BurnAuth { IssuerOnly, OwnerOnly, Both, Neither }
    event Issued(address indexed from, address indexed to, uint256 indexed tokenId, BurnAuth burnAuth);
}

contract NeuroCredit is IERC5484 {

    // ── State ──────────────────────────────────────────────────────────────

    address public owner;
    address public issuer;          // backend oracle wallet

    uint256 private _nextTokenId = 1;

    struct CreditRecord {
        uint256 tokenId;
        uint16  score;              // 300–900
        uint8   grade;              // 0=VeryPoor 1=Poor 2=Fair 3=Good 4=Excellent
        uint32  issuedAt;           // unix timestamp
        uint32  updatedAt;
        bool    eligible;           // lender shortcut
        string  metadataURI;        // IPFS JSON with breakdown
    }

    mapping(address => CreditRecord) private _records;  // wallet → record
    mapping(uint256 => address)      private _owners;   // tokenId → wallet
    mapping(address => bool)         private _hasSBT;

    // ── Events ─────────────────────────────────────────────────────────────

    event ScoreIssued(address indexed wallet, uint256 tokenId, uint16 score, uint8 grade);
    event ScoreUpdated(address indexed wallet, uint16 oldScore, uint16 newScore);
    event IssuerChanged(address indexed oldIssuer, address indexed newIssuer);

    // ── Modifiers ──────────────────────────────────────────────────────────

    modifier onlyOwner()  { require(msg.sender == owner,  "Not owner");  _; }
    modifier onlyIssuer() { require(msg.sender == issuer, "Not issuer"); _; }

    // ── Constructor ────────────────────────────────────────────────────────

    constructor(address _issuer) {
        owner  = msg.sender;
        issuer = _issuer;
    }

    // ── Core: Mint ─────────────────────────────────────────────────────────

    /**
     * @notice Mint a Credit SBT to a wallet. One per address.
     * @param wallet      Recipient wallet address
     * @param score       Credit score (300–900)
     * @param eligible    Whether the applicant qualifies for credit
     * @param metadataURI IPFS URI pointing to full JSON breakdown
     */
    function mintCredit(
        address wallet,
        uint16  score,
        bool    eligible,
        string calldata metadataURI
    ) external onlyIssuer {
        require(wallet != address(0), "Zero address");
        require(score >= 300 && score <= 900, "Invalid score range");
        require(!_hasSBT[wallet], "SBT already issued — use updateScore");

        uint256 tokenId = _nextTokenId++;
        uint8   grade   = _gradeOf(score);

        _records[wallet] = CreditRecord({
            tokenId:     tokenId,
            score:       score,
            grade:       grade,
            issuedAt:    uint32(block.timestamp),
            updatedAt:   uint32(block.timestamp),
            eligible:    eligible,
            metadataURI: metadataURI
        });

        _owners[tokenId] = wallet;
        _hasSBT[wallet]  = true;

        emit Issued(issuer, wallet, tokenId, BurnAuth.IssuerOnly);
        emit ScoreIssued(wallet, tokenId, score, grade);
    }

    // ── Core: Update ───────────────────────────────────────────────────────

    /**
     * @notice Update the score on an existing SBT
     */
    function updateScore(
        address wallet,
        uint16  newScore,
        bool    eligible,
        string calldata metadataURI
    ) external onlyIssuer {
        require(_hasSBT[wallet], "No SBT found — use mintCredit");
        require(newScore >= 300 && newScore <= 900, "Invalid score range");

        uint16 old = _records[wallet].score;
        _records[wallet].score       = newScore;
        _records[wallet].grade       = _gradeOf(newScore);
        _records[wallet].eligible    = eligible;
        _records[wallet].updatedAt   = uint32(block.timestamp);
        _records[wallet].metadataURI = metadataURI;

        emit ScoreUpdated(wallet, old, newScore);
    }

    // ── Read: Verification (public — lenders call this) ───────────────────

    /**
     * @notice Verify a wallet's credit score. No personal data returned.
     * @return score     300–900 numeric score
     * @return grade     0=VeryPoor … 4=Excellent
     * @return eligible  Simple boolean for lenders
     * @return updatedAt Unix timestamp of last update
     */
    function verifyCredit(address wallet) external view returns (
        uint16 score,
        uint8  grade,
        bool   eligible,
        uint32 updatedAt,
        uint256 tokenId
    ) {
        require(_hasSBT[wallet], "No credit SBT found for this address");
        CreditRecord storage r = _records[wallet];
        return (r.score, r.grade, r.eligible, r.updatedAt, r.tokenId);
    }

    function getRecord(address wallet) external view returns (CreditRecord memory) {
        require(_hasSBT[wallet], "No record found");
        return _records[wallet];
    }

    function hasSBT(address wallet) external view returns (bool) {
        return _hasSBT[wallet];
    }

    function ownerOf(uint256 tokenId) external view returns (address) {
        address w = _owners[tokenId];
        require(w != address(0), "Token does not exist");
        return w;
    }

    // ── Transfer lock — SBT cannot be transferred ─────────────────────────

    function transferFrom(address, address, uint256) external pure {
        revert("NeuroCredit: SBTs are non-transferable");
    }

    function safeTransferFrom(address, address, uint256) external pure {
        revert("NeuroCredit: SBTs are non-transferable");
    }

    // ── Admin ──────────────────────────────────────────────────────────────

    function setIssuer(address newIssuer) external onlyOwner {
        emit IssuerChanged(issuer, newIssuer);
        issuer = newIssuer;
    }

    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "Zero address");
        owner = newOwner;
    }

    // ── Internal ───────────────────────────────────────────────────────────

    function _gradeOf(uint16 score) internal pure returns (uint8) {
        if (score >= 800) return 4;
        if (score >= 720) return 3;
        if (score >= 650) return 2;
        if (score >= 580) return 1;
        return 0;
    }

    // ── Metadata ───────────────────────────────────────────────────────────

    function name()   external pure returns (string memory) { return "NeuroCredit SBT"; }
    function symbol() external pure returns (string memory) { return "NCSBT"; }
}
