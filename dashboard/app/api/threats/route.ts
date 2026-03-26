import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET() {
  // We go up one level from 'dashboard' to find the Python brain's JSON file
  const filePath = path.join(process.cwd(), '..', 'control-plane', 'threat_feed.json');
  
  try {
    if (fs.existsSync(filePath)) {
      const fileContents = fs.readFileSync(filePath, 'utf8');
      const data = JSON.parse(fileContents);
      return NextResponse.json(data);
    }
    return NextResponse.json([]); // Return an empty array if the file doesn't exist yet
  } catch (error) {
    console.error("Error reading threat feed:", error);
    return NextResponse.json({ error: 'Failed to read threat feed' }, { status: 500 });
  }
}