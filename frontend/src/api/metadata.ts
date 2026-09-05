import client from './client'
import type {MetadataResponse} from '../types/records'

export async function fetchResourceMetadata(): Promise<MetadataResponse> {
  const { data } = await client.get<MetadataResponse>('/metadata/resources/')
  return data
}
